from atomicwrites import atomic_write

import os

from subwinder import utils
from subwinder._ranking import rank_guess_media, rank_search_subtitles
from subwinder._request import request, Endpoints
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
    SearchResult,
    ServerInfo,
)
from subwinder.lang import lang_2s, lang_3s, lang_longs, LangFormat
from subwinder.media import Media


def _build_search_query(query, lang):
    # All queries take a language
    internal_query = {"sublanguageid": lang_2s.convert(lang, LangFormat.LANG_3)}

    # Handle all the different formats for seaching for subtitles
    if isinstance(query, Media):
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
        raise ValueError(f"`_build_search_query` does not take type of '{type(query)}'")

    return internal_query


def _batch(function, batch_size, iterables, *args, **kwargs):
    results = []
    for i in range(0, len(iterables[0]), batch_size):
        chunked = []
        for iterable in iterables:
            chunked.append(iterable[i : i + batch_size])

        result = function(*chunked, *args, **kwargs)
        if result is not None:
            results += result

    return results


class Subwinder:
    _token = None

    def __repr__(self):
        return f"{self.__class__.__name__}"

    def _request(self, method, *params):
        # Call the `request` function with our token
        return request(method, self._token, *params)

    def daily_download_info(self):
        return self.server_info().daily_download_info

    def get_languages(self):
        return list(zip(lang_2s, lang_3s, lang_longs))

    def server_info(self):
        return ServerInfo.from_data(self._request(Endpoints.SERVER_INFO))


class AuthSubwinder(Subwinder):
    def __init__(self, username=None, password=None, useragent=None):
        # Try to get any info from env vars if not passed in
        useragent = useragent or os.environ.get("OPEN_SUBTITLES_USERAGENT")
        username = username or os.environ.get("OPEN_SUBTITLES_USERNAME")
        password = password or os.environ.get("OPEN_SUBTITLES_PASSWORD")

        if username is None:
            raise SubAuthError(
                "missing `username`, set when initializing `AuthSubwinder` or with the"
                " OPEN_SUBTITLES_USERNAME env var"
            )

        if password is None:
            raise SubAuthError(
                "missing `password`, set when initializing `AuthSubwinder` or set the"
                " OPEN_SUBTITLES_PASSWORD env var"
            )

        if useragent is None:
            raise SubAuthError(
                "missing `useragent`, set when initializing `AuthSubwinder` or set the"
                " OPEN_SUBTITLES_USERAGENT env var. `useragent` must be specified for"
                " your app according to instructions given at"
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
        resp = self._request(Endpoints.LOG_IN, username, password, "en", useragent)
        return resp["token"]

    def _logout(self):
        self._request(Endpoints.LOG_OUT)
        self._token = None

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
                    "Insufficient context. Need to set either the `dirname` in"
                    f" {download} or `download_dir` in `download_subtitles`"
                )

            if media.filename is None:
                # Hacky way to see if `media_name` is used in `name_format`
                try:
                    _ = name_format.format(
                        lang_2="",
                        lang_3="",
                        ext="",
                        upload_name="",
                        upload_filename="",
                    )
                except KeyError:
                    # Can't set the media's `media_name` if we have no `media_name`
                    raise SubDownloadError(
                        "Insufficient context. Need to set the `filename` for"
                        f" {download} if you plan on using `media_name` in the"
                        " `name_format`"
                    )

            # Store the subtitle file next to the original media unless `download_dir`
            # was set
            if download_dir is None:
                dir_path = media.dirname
            else:
                dir_path = os.fspath(download_dir)

            # Format the `filename` according to the `name_format` passed in
            media_name = None if media.filename is None else media.filename.stem
            upload_name = subtitles.filename.stem

            filename = name_format.format(
                media_name=media_name,
                lang_2=subtitles.lang_2,
                lang_3=subtitles.lang_3,
                ext=subtitles.ext,
                upload_name=upload_name,
                upload_filename=subtitles.filename,
            )

            download_paths.append(dir_path / filename)

        # Check that the user has enough downloads remaining to satisfy all
        # `downloads`
        daily_remaining = self.daily_download_info().remaining
        if daily_remaining < len(downloads):
            raise SubDownloadError(
                f"Not enough daily downloads remaining ({daily_remaining} <"
                f" {len(downloads)})"
            )

        # Download the subtitles in batches of 20, per api spec
        _batch(self._download_subtitles, 20, [downloads, download_paths])

        # Return the list of paths where subtitle files were saved
        return download_paths

    def _download_subtitles(self, downloads, filepaths):
        encodings = []
        sub_file_ids = []
        # Unpack stored info
        for search_result in downloads:
            encodings.append(search_result.subtitles.encoding)
            sub_file_ids.append(search_result.subtitles.file_id)

        data = self._request(Endpoints.DOWNLOAD_SUBTITLES, sub_file_ids)["data"]

        for encoding, result, fpath in zip(encodings, data, filepaths):
            # Currently pray that python supports all the encodings and is called the
            # same as what opensubtitles returns
            subtitles = utils.extract(result["data"], encoding)

            # Create the directories if needed, then save the file
            dirpath = fpath.parent
            dirpath.mkdir(exist_ok=True)
            with atomic_write(fpath) as f:
                f.write(subtitles)

    def get_comments(self, search_results):
        subtitle_ids = [s.subtitles.id for s in search_results]
        data = self._request(Endpoints.GET_COMMENTS, subtitle_ids)["data"]

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
            comments.append([Comment.from_data(c) for c in raw_comments])

        return comments

    def user_info(self):
        return FullUserInfo.from_data(self._request(Endpoints.GET_USER_INFO)["data"])

    def ping(self):
        self._request(Endpoints.NO_OPERATION)

    def guess_media(
        self, queries, ranking_func=rank_guess_media, *rank_args, **rank_kwargs,
    ):
        VALID_CLASSES = (list, tuple)
        if not isinstance(queries, VALID_CLASSES):
            raise ValueError(
                "`guess_media` expects `queries` to be of type included in"
                f" {VALID_CLASSES}, but got type '{type(queries)}'"
            )

        # Batch to 3 per api spec
        return _batch(
            self._guess_media, 3, [queries], ranking_func, *rank_args, **rank_kwargs,
        )

    def _guess_media(self, queries, ranking_func, *rank_args, **rank_kwargs):
        data = self._request(Endpoints.GUESS_MOVIE_FROM_STRING, queries)["data"]

        results = []
        for query in queries:
            result = ranking_func(data[query], query, *rank_args, **rank_kwargs)

            # Build the correct media info if anything was returned
            results.append(None if result is None else build_media_info(result))

        return results

    def report_movie(self, search_result):
        self._request(
            Endpoints.REPORT_WRONG_MOVIE_HASH, search_result.subtitles.sub_to_movie_id
        )

    def search_subtitles(
        self, queries, ranking_func=rank_search_subtitles, *rank_args, **rank_kwargs,
    ):
        # Verify that all the queries are correct before doing any requests
        VALID_CLASSES = (Media, MovieInfo, EpisodeInfo)
        for query, lang_2 in queries:
            if not isinstance(query, VALID_CLASSES):
                raise ValueError(
                    "`search_subtitles` expects `queries` to contain objects"
                    f" of {VALID_CLASSES}, but got type '{type(query)}'"
                )

            if lang_2 not in lang_2s:
                # Show both the 2-char and long name if invalid lang is given
                lang_map = [f"{k} -> {v}" for k, v in zip(lang_2s, lang_longs)]
                lang_map = "\n".join(lang_map)

                raise SubLangError(
                    f"'{lang_2}' not found in valid lang list:\n{lang_map}"
                )

        # This can return 500 items, but one query could return multiple so 20 is being
        # used in hope that there are plenty of results for each
        return _batch(
            self._search_subtitles,
            20,
            [queries],
            ranking_func,
            *rank_args,
            **rank_kwargs,
        )

    def _search_subtitles(self, queries, ranking_func, *rank_args, **rank_kwargs):
        internal_queries = [_build_search_query(q, l) for q, l in queries]
        data = self._request(Endpoints.SEARCH_SUBTITLES, internal_queries)["data"]

        # Go through the results and organize them in the order of `queries`
        groups = [[] for _ in internal_queries]
        for d in data:
            groups[int(d["QueryNumber"])].append(d)

        search_results = []
        for group, (query, _) in zip(groups, queries):
            result = ranking_func(group, query, *rank_args, **rank_kwargs)

            # Get `SearchResult` setup if there is info for one
            search_result = None
            if result is not None:
                search_result = SearchResult.from_data(result)
                if isinstance(query, Media):
                    # Media could have the original file information tied to it
                    search_result.media.dirname = query.dirname
                    search_result.media.filename = query.filename

            search_results.append(search_result)

        return search_results

    def suggest_media(self, query):
        data = self._request(Endpoints.SUGGEST_MOVIE, query)["data"]

        # `data` is an empty list if there were no results
        return [] if not data else [build_media_info(media) for media in data[query]]

    def add_comment(self, search_result, comment_str, bad=False):
        self._request(
            Endpoints.ADD_COMMENT, search_result.subtitles.id, comment_str, bad
        )

    def vote(self, search_result, score):
        if score < 2 or score > 10:
            raise ValueError(f"Subtitle Vote must be between 1 and 10, given '{score}'")

        self._request(Endpoints.SUBTITLES_VOTE, search_result.subtitles.id, score)

    def auto_update(self, program_name):
        # Not sure if I should return this information in a better format
        return self._request(Endpoints.AUTO_UPDATE, program_name)

    def preview_subtitles(self, queries):
        ids = [q.subtitles.file_id for q in queries]

        # Batch to 20 per api spec
        return _batch(self._preview_subtitles, 20, [ids])

    def _preview_subtitles(self, ids):
        data = self._request(Endpoints.PREVIEW_SUBTITLES, ids)["data"]

        # Unpack our data
        previews = []
        for preview in data:
            encoding = preview["encoding"]
            contents = preview["contents"]

            previews.append(utils.extract(contents, encoding))

        return previews
