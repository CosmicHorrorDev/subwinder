# TODO: try to switch movie to media in places where it could be a movie or
#       episode
# TODO: not really an easy way to re-get a subtitle result, best option without
#       the lib user saving info is to do another search on the movie and
#       matching the subhash again, but that's not very flexible or nice so ask
#       the devs if there is a nicer way
# TODO: handle selecting result from checkmoviehash like search result, where
#       a custom ranking function can be used, if not provided use the default
#       results

import os

from subwinder import utils
from subwinder.base import SubWinder
from subwinder.constants import _LANG_2, _LANG_2_TO_3
from subwinder.info import Comment, FullUserInfo, MediaInfo
from subwinder.exceptions import (
    SubAuthError,
    SubLangError,
)
from subwinder.results import SearchResult


# TODO: go through all the lang_3 options and get the equivalent lang_2 so that
#       it can be converted correctly


# FIXME: rank by highest score?
def _default_ranking(results, query_index, exclude_bad=True, sub_exts=None):
    best_result = None
    max_downloads = None
    DOWN_KEY = "SubDownloadsCnt"

    # Force list of `sub_exts` to be lowercase
    if sub_exts is not None:
        sub_exts = [sub_ext.lower() for sub_ext in sub_exts]

    for result in results:
        # Skip if someone listed sub as bad and `exclude_bad` is `True`
        if exclude_bad and result["SubBad"] != "0":
            continue

        # Skip incorrect `sub_ext`s if provided
        if sub_exts is not None:
            if result["SubFormat"].lower() not in sub_exts:
                continue

        if max_downloads is None or int(result[DOWN_KEY]) > max_downloads:
            best_result = result
            max_downloads = int(result[DOWN_KEY])

    return best_result


class AuthSubWinder(SubWinder):
    def __init__(self, useragent, username=None, password=None):
        # Try to get any info from env vars if not passed in
        username = username or os.environ.get("OPEN_SUBTITLES_USERNAME")
        password = password or os.environ.get("OPEN_SUBTITLES_PASSWORD")

        if username is None or password is None:
            raise SubAuthError("username or password is missing")

        if not useragent:
            raise SubAuthError(
                "`useragent` must be sepcified for your app according to"
                " instructions given at https://trac.opensubtitles.org/"
                "projects/opensubtitles/wiki/DevReadFirst"
            )

        self._token = self._login(username, password, useragent)

    def _login(self, username, password, useragent):
        resp = self._request("LogIn", username, password, "en", useragent)
        return resp["token"]

    # FIXME: this should be done on exiting `with`
    def _logout(self):
        self._request("LogOut")

    # TODO: unless I'm missing an endpoint option this isn't useful externally
    #       can be used internally though
    # Note: This doesn't look like it batches (likely because it's use is very
    #       limited)
    def check_subtitles(self, subtitles_hashers):
        # Get all of the subtitles_ids from the hashes
        hashes = [s.hash for s in subtitles_hashers]
        data = self._request("CheckSubHash", hashes)["data"]
        subtitles_ids = [data[h] for h in hashes]
        return subtitles_ids

    def download_subtitles(
        self, downloads, download_dir=None, name_format="{upload_filename}"
    ):
        # List of paths where the subtitle files should be saved
        download_paths = []
        for download in downloads:
            # Store the subtitle file next to the original media unless
            # `download_dir` was set
            if download_dir is None:
                dir_path = os.path.dirname(download.media_filepath)
            else:
                dir_path = download_dir

            # Format the `filename` according to the `name_format` passed in
            subtitles = download.subtitles
            media_filename = os.path.basename(download.media_filepath)
            media_name, _ = os.path.splitext(media_filename)
            upload_name, _ = os.path.splitext(subtitles.media_filename)

            filename = name_format.format(
                **{
                    "media_name": media_name,
                    "lang_2": subtitles.lang_2,
                    "lang_3": subtitles.lang_3,
                    "ext": subtitles.ext,
                    "upload_name": upload_name,
                    "upload_filename": subtitles.media_filename,
                }
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

    # TODO: does this need to be batched
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

    def guess_media(self, queries):
        BATCH_SIZE = 3
        results = []
        for i in range(0, len(queries), BATCH_SIZE):
            results += self._guess_media(queries[i : i + BATCH_SIZE])

        return results

    def _guess_media(self, queries):
        data = self._request("GuessMovieFromString", queries)["data"]

        # TODO: is there a better return type for this?
        return [MediaInfo(data[q]["BestGuess"]) for q in queries]

    def report_movie(self, search_result):
        self._request(
            "ReportWrongMovieHash", search_result.subtitles.sub_to_movie_id
        )

    def search_subtitles(
        self, queries, *, ranking_function=_default_ranking, **rank_params
    ):
        # Verify that all the languages are correct before doing any requests
        for _, lang_2 in queries:
            if lang_2 not in _LANG_2:
                # TODO: may want to include the long names as well to make it
                #       easier for people to find the correct lang_2
                raise SubLangError(
                    f"'{lang_2}' not found in valid lang list: {_LANG_2}"
                )

        # This can return 500 items, but one query could return multiple so
        # 20 is being used in hope that there are plenty of results for each
        BATCH_SIZE = 20
        results = []
        for i in range(0, len(queries), BATCH_SIZE):
            results += self._search_subtitles(
                queries[i : i + BATCH_SIZE], ranking_function, **rank_params
            )

        return results

    def _search_subtitles(
        self, queries, ranking_function=_default_ranking, **rank_params
    ):
        internal_queries = []
        for movie, lang in queries:
            # Search by movie's hash and size
            internal_queries.append(
                {
                    "sublanguageid": _LANG_2_TO_3[lang],
                    "moviehash": movie.hash,
                    "moviebytesize": str(movie.size),
                }
            )

        data = self._request("SearchSubtitles", internal_queries)["data"]

        # Go through the results and organize them in the order of `queries`
        groups = [[] for _ in internal_queries]
        for d in data:
            query_index = int(d["QueryNumber"])
            groups[query_index].append(d)

        search_results = []
        for group, (query, _) in zip(groups, queries):
            result = ranking_function(group, query, **rank_params)

            if result is None:
                search_results.append(None)
            else:
                search_results.append(SearchResult(result, query.filepath))

        return search_results

    def suggest_media(self, query):
        data = self._request("SuggestMovie", query)["data"]
        raw_movies = data[query]

        # TODO: is there a better to set up the class for this?
        return [MediaInfo(r_m) for r_m in raw_movies]

    def add_comment(self, subtitle_id, comment_str, bad=False):
        # TODO: magically get the subtitle id from the result
        raise NotImplementedError
        self._request("AddComment", subtitle_id, comment_str, bad)
