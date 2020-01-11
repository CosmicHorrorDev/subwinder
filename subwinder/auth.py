import os

from subwinder import utils
from subwinder.base import SubWinder
from subwinder.exceptions import (
    SubAuthError,
    SubDownloadError,
    SubLangError,
)
from subwinder.info import (
    build_media_info,
    Comment,
    EpisodeInfo,
    FullUserInfo,
    MovieInfo,
)
from subwinder.lang import lang_2s, LangFormat
from subwinder.media import Media
from subwinder.ranking import _rank_guess_media, _rank_search_subtitles
from subwinder.results import SearchResult


def _build_search_query(query, lang):
    # All queries take a language
    internal_query = {
        "sublanguageid": lang_2s.convert(lang, LangFormat.LANG_3)
    }

    # Handle all the different formats for seaching for subtitles
    if type(query) == Media:
        # Search by `Media`s hash and size
        internal_query["moviehash"] = query.hash
        internal_query["moviebytesize"] = str(query.size)
    elif isinstance(query, (MovieInfo, EpisodeInfo)):
        # All `MediaInfo` classes provide an `imdbid`
        internal_query["imdbid"] = query.imdbid

        # `EpisodeInfo` also needs a `season` and `episode`
        if isinstance(query, EpisodeInfo):
            internal_query["season"] = query.season
            internal_query["episode"] = query.episode
    else:
        raise ValueError(
            f"`_build_search_query` does not take type of {query}"
        )

    return internal_query


class AuthSubWinder(SubWinder):
    def __init__(self, username=None, password=None, useragent=None):
        # Try to get any info from env vars if not passed in
        useragent = useragent or os.environ.get("OPEN_SUBTITLES_USERAGENT")
        username = username or os.environ.get("OPEN_SUBTITLES_USERNAME")
        password = password or os.environ.get("OPEN_SUBTITLES_PASSWORD")

        if username is None:
            raise SubAuthError(
                "missing `username`, set when initializing `AuthSubWinder` or"
                " with the OPEN_SUBTITLES_USERNAME env var"
            )

        if password is None:
            raise SubAuthError(
                "missing `password`, set when initializing `AuthSubWinder` or"
                " set the OPEN_SUBTITLES_PASSWORD env var"
            )

        if useragent is None:
            raise SubAuthError(
                "missing `useragent`, set when initializing `AuthSubWinder` or"
                " set the OPEN_SUBTITLES_USERAGENT env var. `useragent` must"
                " be sepcified for your app according to instructions given at"
                " https://trac.opensubtitles.org/projects/opensubtitles/wiki/"
                "DevReadFirst"
            )

        self._token = self._login(username, password, useragent)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Logout on exiting `with` if all is well
        if exc_type is None:
            self._logout()

    def __repr__(self):
        return f"{self.__class__.__name__}(_token: {self._token.__repr__()})"

    def _login(self, username, password, useragent):
        resp = self._request("LogIn", username, password, "en", useragent)
        return resp["token"]

    def _logout(self):
        self._request("LogOut")
        self._token = None

    # TODO: unless I'm missing an endpoint option this isn't useful externally
    #       can be used internally though
    # Note: This doesn't look like it batches (likely because it's use is very
    #       limited)
    def check_subtitles(self, subtitles_hashers):
        # Get all of the subtitles_ids from the hashes
        hashes = [s.hash for s in subtitles_hashers]
        data = self._request("CheckSubHash", hashes)["data"]
        subtitles_ids = [data[h] for h in hashes]

        # Subtitle id "0" means no subtitle match so return as `None`
        return [sub_id if sub_id != "0" else None for sub_id in subtitles_ids]

    def download_subtitles(
        self, downloads, download_dir=None, name_format="{upload_filename}"
    ):
        # List of paths where the subtitle files should be saved
        download_paths = []
        for download in downloads:
            media = download.media
            subtitles = download.subtitles

            # Make sure there is enough context to save subtitles
            if media.dirname is None and download_dir is None:
                raise SubDownloadError(
                    "Insufficient context. Need to set either the `dirname`"
                    f" in {download} or `download_dir` in `download_subtitles`"
                )

            # Hacky way to tell if `media_name` is used in `name_format`
            try_format = name_format.format(
                media_name="",
                lang_2="{lang_2}",
                lang_3="{lang_3}",
                ext="{ext}",
                upload_name="{upload_name}",
                upload_filename="{upload_filename}",
            )
            if media.filename is None and try_format != name_format:
                raise SubDownloadError(
                    "Insufficient context. Need to set either the `filename`"
                    f" in {download} or avoid using '{{media_name}}' in"
                    " `name_format`"
                )

            # Store the subtitle file next to the original media unless
            # `download_dir` was set
            if download_dir is None:
                dir_path = media.dirname
            else:
                dir_path = download_dir

            # Format the `filename` according to the `name_format` passed in
            media_name, _ = os.path.splitext(media.filename)
            upload_filename = subtitles.filename
            upload_name, _ = os.path.splitext(upload_filename)

            filename = name_format.format(
                media_name=media_name,
                lang_2=subtitles.lang_2,
                lang_3=subtitles.lang_3,
                ext=subtitles.ext,
                upload_name=upload_name,
                upload_filename=upload_filename,
            )

            download_paths.append(os.path.join(dir_path, filename))

        # Download the subtitles in batches of 20, per api spec
        BATCH_SIZE = 20
        for i in range(0, len(downloads), BATCH_SIZE):
            download_chunk = downloads[i : i + BATCH_SIZE]
            paths_chunk = download_paths[i : i + BATCH_SIZE]
            self._download_subtitles(download_chunk, paths_chunk)

        # Return the list of paths where subtitle files were saved
        return download_paths

    def _download_subtitles(self, downloads, filepaths):
        encodings = []
        sub_file_ids = []
        # Unpack stored info
        for search_result in downloads:
            encodings.append(search_result.subtitles.encoding)
            sub_file_ids.append(search_result.subtitles.file_id)

        data = self._request("DownloadSubtitles", sub_file_ids)["data"]

        for encoding, result, fpath in zip(encodings, data, filepaths):
            # Currently pray that python supports all the encodings and is
            # called the same as what opensubtitles returns
            subtitles = utils.extract(result["data"], encoding)

            # Create the directories if needed, then save the file
            dirpath = os.path.dirname(fpath)
            os.makedirs(dirpath, exist_ok=True)
            with open(fpath, "w") as f:
                f.write(subtitles)

    def get_comments(self, search_results):
        subtitle_ids = [s.subtitles.id for s in search_results]
        data = self._request("GetComments", subtitle_ids)["data"]

        # Group the results, if any, by the query order
        groups = [[] for _ in search_results]
        if data:
            for id, comments in data.items():
                # Returned `id` has a leading _ for some reason so strip it
                index = subtitle_ids.index(id[1:])
                groups[index] = data[id]

        # Pack results, if any, into `Comment` objects
        comments = []
        for raw_comments in groups:
            if not raw_comments:
                comments.append([])
            else:
                comments.append([Comment(c) for c in raw_comments])

        return comments

    def user_info(self):
        data = self._request("GetUserInfo")["data"]
        return FullUserInfo(data)

    def ping(self):
        self._request("NoOperation")

    def guess_media(
        self, queries, ranking_func=_rank_guess_media, **rank_params
    ):
        VALID_CLASSES = (list, tuple)
        if not isinstance(queries, VALID_CLASSES):
            raise ValueError(
                f"`guess_media` expects `queries` of type {VALID_CLASSES}, but"
                f" saw type {type(queries)} instead"
            )

        BATCH_SIZE = 3
        results = []
        for i in range(0, len(queries), BATCH_SIZE):
            results += self._guess_media(
                queries[i : i + BATCH_SIZE], ranking_func, **rank_params
            )

        return results

    def _guess_media(self, queries, ranking_func, **rank_params):
        data = self._request("GuessMovieFromString", queries)["data"]

        results = []
        for query in queries:
            result = ranking_func(data[query], query)

            if result is None:
                results.append(None)
            else:
                results.append(build_media_info(result))

        return results

    def report_movie(self, search_result):
        self._request(
            "ReportWrongMovieHash", search_result.subtitles.sub_to_movie_id
        )

    def search_subtitles(
        self, queries, *, ranking_func=_rank_search_subtitles, **rank_params
    ):
        # Verify that all the queries are correct before doing any requests
        VALID_CLASSES = (Media, MovieInfo, EpisodeInfo)
        for query, lang_2 in queries:
            if not isinstance(query, VALID_CLASSES):
                raise ValueError(
                    f"`search_subtitles` takes one of {VALID_CLASSES}, but it"
                    f" was given {query}"
                )

            if lang_2 not in list(lang_2s):
                # TODO: may want to include the long names as well to make it
                #       easier for people to find the correct lang_2
                raise SubLangError(
                    f"'{lang_2}' not found in valid lang list:"
                    f" {list(lang_2s)}"
                )

        # This can return 500 items, but one query could return multiple so
        # 20 is being used in hope that there are plenty of results for each
        BATCH_SIZE = 20
        results = []
        for i in range(0, len(queries), BATCH_SIZE):
            results += self._search_subtitles(
                queries[i : i + BATCH_SIZE], ranking_func, **rank_params
            )

        return results

    def _search_subtitles(self, queries, ranking_func, **rank_params):
        internal_queries = [_build_search_query(q, l) for q, l in queries]
        data = self._request("SearchSubtitles", internal_queries)["data"]

        # Go through the results and organize them in the order of `queries`
        groups = [[] for _ in internal_queries]
        for d in data:
            query_index = int(d["QueryNumber"])
            groups[query_index].append(d)

        search_results = []
        for group, (query, _) in zip(groups, queries):
            result = ranking_func(group, query, **rank_params)

            if result is None:
                search_results.append(None)
            else:
                if type(query) == Media:
                    # Media could have the original file information tied to it
                    search_results.append(
                        SearchResult(result, query.dirname, query.filename)
                    )
                else:
                    search_results.append(SearchResult(result))

        return search_results

    def suggest_media(self, query):
        data = self._request("SuggestMovie", query)["data"]

        # Returns an empty list for no results
        if not data:
            return data

        raw_movies = data[query]
        return [build_media_info(r_m) for r_m in raw_movies]

    def add_comment(self, subtitle_id, comment_str, bad=False):
        raise NotImplementedError
        self._request("AddComment", subtitle_id, comment_str, bad)
