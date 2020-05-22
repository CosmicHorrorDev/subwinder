# Optional dependency: atomic_downloads
try:
    from atomicwrites import atomic_write

    ATOMIC_DOWNLOADS_SUPPORT = True
except ImportError:
    ATOMIC_DOWNLOADS_SUPPORT = False


from pathlib import Path
import os

from subwinder import utils
from subwinder._internal_utils import type_check
from subwinder._request import request, Endpoints
from subwinder.exceptions import SubAuthError, SubDownloadError, SubLangError
from subwinder.info import (
    build_media_info,
    Comment,
    EpisodeInfo,
    FullUserInfo,
    GuessMediaResult,
    MediaInfo,
    MovieInfo,
    SearchResult,
    ServerInfo,
    SubtitlesInfo,
)
from subwinder.lang import lang_2s, lang_3s, lang_longs, LangFormat
from subwinder.media import Media
from subwinder.ranking import rank_guess_media, rank_search_subtitles


def _build_search_query(query, lang):
    """
    Helper function for `AuthSubwinder.search_subtitles(...)` that handles converting
    the `query` to the appropriate `dict` of information for the API.
    """
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
    """
    Helper function that batches calls of `function` with at most `batch_size` amount of
    `iterables` each call. Both `args` and `kwargs` will be passed in directly.
    """
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
    """
    The class used for all unauthenticated functionality exposed by the library.
    """

    _token = None

    def __repr__(self):
        return f"{self.__class__.__name__}"

    def _request(self, endpoint, *params):
        """
        Call the API `Endpoint` represented by `method` with any of the given `params`.
        """
        # Call the `request` function with our token
        return request(endpoint, self._token, *params)

    def daily_download_info(self):
        """
        Returns `DownloadInfo` for the current client.
        """
        return self.server_info().daily_download_info

    def get_languages(self):
        """
        Gets a list of the supported languages for the API in their various formats.
        """
        return list(zip(lang_2s, lang_3s, lang_longs))

    def server_info(self):
        """
        Returns `ServerInfo` for the opensubtitles.
        """
        return ServerInfo.from_data(self._request(Endpoints.SERVER_INFO))


class AuthSubwinder(Subwinder):
    """
    The class used for all authenticated and unauthenticated functionality exposed by
    the library.
    """

    def __init__(self, username=None, password=None, useragent=None):
        """
        Signs in the user with the given `username`, `password` and program's
        `useragent`. These can also be set as environment variables instead if that's
        preferable. If the parameter is passed in and the env var is set then the
        parameter is used.
        """
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
        """
        Handles logging in the user with the provided information and storing the auth
        token. Automatically called by `__init__` so no need to call it directly.
        """
        resp = self._request(Endpoints.LOG_IN, username, password, "en", useragent)
        return resp["token"]

    def _logout(self):
        """
        Attempts to log out the user from the current session. Automatically called on
        exiting `with` so no need to call it directly.
        """
        self._request(Endpoints.LOG_OUT)
        self._token = None

    def download_subtitles(
        self, downloads, download_dir=None, name_format="{upload_filename}"
    ):
        """
        Attempts to download the `SearchResult`s passed in as `downloads`. The download
        will attempt to place files in the same directory as the original file unless
        `download_dir` is provided. Files are automatically named according to the
        provided `name_format`.
        """
        type_check(downloads, (list, tuple))

        # Get all the subtitle file_ids from `downloads`
        # List of paths where the subtitle files should be saved
        download_paths = []
        for download in downloads:
            # All downloads should be some container for `SubtitlesInfo`
            type_check(download, (SearchResult, SubtitlesInfo))
            if isinstance(download, SearchResult):
                media = download.media
                subtitles = download.subtitles
            else:
                subtitles = download
                # There's no original media so fake it
                media = MediaInfo.__new__(MediaInfo)
                media.dirname = None
                media.filename = None

            # Make sure there is enough context to save subtitles
            if media.get_dirname() is None and download_dir is None:
                raise SubDownloadError(
                    "Insufficient context. Need to set either the `dirname` in"
                    f" {download} or `download_dir` in `download_subtitles`"
                )

            if media.get_filename() is None:
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
                dir_path = media.get_dirname()
            else:
                dir_path = Path(download_dir)

            # Format the `filename` according to the `name_format` passed in
            upload_name = subtitles.filename.stem
            if media.get_filename() is None:
                media_name = None
            else:
                media_name = media.get_filename().stem

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

            # Write atomically if possible, otherwise fall back to regular writing
            if ATOMIC_DOWNLOADS_SUPPORT:
                with atomic_write(fpath) as f:
                    f.write(subtitles)
            else:
                with fpath.open("w") as f:
                    f.write(subtitles)

    def get_comments(self, sub_containers):
        """
        Get all `Comment`s for the provided `search_results` if there are any.
        """
        type_check(sub_containers, (list, tuple))

        ids = []
        for sub_container in sub_containers:
            type_check(sub_container, (SearchResult, SubtitlesInfo))

            if isinstance(sub_container, SearchResult):
                sub_container = sub_container.subtitles
            ids.append(sub_container.id)
        data = self._request(Endpoints.GET_COMMENTS, ids)["data"]

        # Group the results, if any, by the query order
        groups = [[] for _ in sub_containers]
        if data:
            for id, comments in data.items():
                # Returned `id` has a leading _ for some reason so strip it
                index = ids.index(id[1:])
                groups[index] = data[id]

        # Pack results, if any, into `Comment` objects
        comments = []
        for raw_comments in groups:
            comments.append([Comment.from_data(c) for c in raw_comments])

        return comments

    def user_info(self):
        """
        Get information stored for the current user.
        """
        return FullUserInfo.from_data(self._request(Endpoints.GET_USER_INFO)["data"])

    def ping(self):
        """
        Pings the API to keep the session active. Sessions will automatically end after
        15 minutes of inactivity so this can be used to keep a session alive if there's
        no meaningful work to do.
        """
        self._request(Endpoints.NO_OPERATION)

    def guess_media(
        self, queries, ranking_func=rank_guess_media, *rank_args, **rank_kwargs,
    ):
        """
        Same as `guess_media_unranked`, but selects the best result using `ranking_func`
        """
        results = self.guess_media_unranked(queries)

        selected = []
        for result, query in zip(results, queries):
            selected.append(ranking_func(result, query, *rank_args, **rank_kwargs))

        return selected

    def guess_media_unranked(self, queries):
        """
        Attempts to guess the media described by each of the `queries`. A custom ranking
        function can be provided to better match the result with `ranking_func` where
        parameters can be passed to this function using `*args` and `**kwargs`.
        """
        type_check(queries, (list, tuple))

        # Batch to 3 per api spec
        return _batch(self._guess_media_unranked, 3, [queries])

    def _guess_media_unranked(self, queries):
        data = self._request(Endpoints.GUESS_MOVIE_FROM_STRING, queries)["data"]

        # Special case: so `""` is just silently excluded from the response so force it
        if "" in queries and "" not in data:
            data[""] = {}

        # Convert the raw results to `GuessMediaResult`
        return [GuessMediaResult.from_data(data[query]) for query in queries]

    # TODO: can we ensure that the `search_result` was matched using a file hash before
    #       calling this endpoint
    def report_media(self, sub_container):
        """
        Reports the subtitles tied to the `search_result`. This can only be done if the
        match was done using a `Media` object so that the subtitles can be tied to a
        specific file. There's a number of good situations to use this like if the
        subtitles were listed under the wrong language, are for the wrong movie, or
        aren't in sync. If theyre OK, but have lots of mistakes or something then it
        would be better to add a comment instead to give context as to why they're bad
        (`.add_comment("<meaningful-comment>", bad=True)`).
        """
        type_check(sub_container, (SearchResult, SubtitlesInfo))

        # Get subtitles file_id from `sub_container`
        if isinstance(sub_container, SearchResult):
            sub_container = sub_container.subtitles
        sub_to_movie_id = sub_container.sub_to_movie_id

        # This endpoint should only be used when the subtitles were matched by hash
        if sub_to_movie_id is None:
            raise ValueError(
                "`report_media` can only be called if the subtitles were matched off a"
                " search using a media files hash and size (This is done automatically"
                " when searching with a `Media` object)."
            )

        self._request(Endpoints.REPORT_WRONG_MOVIE_HASH, sub_to_movie_id)

    def search_subtitles(
        self, queries, ranking_func=rank_search_subtitles, *rank_args, **rank_kwargs,
    ):
        """
        Same as `search_subtitles_unranked`, but the results are run through the
        `ranking_func` first to try and determine the best result.
        """
        # Get all the results for the query
        groups = self.search_subtitles_unranked(queries)

        # And select the best results with the `ranking_func`
        selected = []
        for group, (query, _) in zip(groups, queries):
            selected.append(ranking_func(group, query, *rank_args, **rank_kwargs))

        return selected

    def search_subtitles_unranked(self, queries):
        """
        Searches for any subtitles that match the provided `queries`. Queries are
        allowed to be `Media`, `MovieInfo`, or `EpisodeInfo` objects. A custom ranking
        function for matching a result can be provided through `ranking_func` which also
        gets passed the provided `*args` and `**kwargs`.
        """
        # Verify that all the queries are correct before doing any requests
        type_check(queries, (list, tuple, zip))

        # Expand out the `zip` to a `list`
        if isinstance(queries, zip):
            queries = list(zip)

        VALID_CLASSES = (Media, MovieInfo, EpisodeInfo)
        for query_pair in queries:
            if not isinstance(query_pair, (list, tuple)) or len(query_pair) == 2:
                raise ValueError(
                    "The `search_subtitles` variants expect a list of pairs of the form"
                    "(<queryable>, <2 letter language code>)"
                )

            query, lang_2 = query_pair
            type_check(query, VALID_CLASSES)

            if lang_2 not in lang_2s:
                # Show both the 2-char and long name if invalid lang is given
                lang_map = [f"{k} -> {v}" for k, v in zip(lang_2s, lang_longs)]
                lang_map = "\n".join(lang_map)

                raise SubLangError(
                    f"'{lang_2}' not found in valid lang list:\n{lang_map}"
                )

        # This can return 500 items, but one query could return multiple so 20 is being
        # used in hope that there are plenty of results for each
        return _batch(self._search_subtitles_unranked, 20, [queries],)

    def _search_subtitles_unranked(self, queries):
        internal_queries = [_build_search_query(q, l) for q, l in queries]
        data = self._request(Endpoints.SEARCH_SUBTITLES, internal_queries)["data"]

        # Go through the results and organize them in the order of `queries`
        groups = [[] for _ in internal_queries]
        for raw_result in data:
            # Results are returned in an arbitrary order so first figure out the query
            query_index = int(raw_result["QueryNumber"])
            query, _ = queries[query_index]

            # Go ahead and format the result as a `SearchResult`
            result = SearchResult.from_data(raw_result)
            result.media.set_dirname(query.get_dirname())
            result.media.set_filename(query.get_filename())

            groups[query_index].append(result)

        return groups

    def suggest_media(self, query):
        """
        Suggest results for guesses of what media is described by `query`.
        """
        type_check(query, str)

        data = self._request(Endpoints.SUGGEST_MOVIE, query)["data"]

        # `data` is an empty list if there were no results
        return [] if not data else [build_media_info(media) for media in data[query]]

    def add_comment(self, sub_container, comment_str, bad=False):
        """
        Adds the comment `comment_str` for the `search_result`. If desired you can
        denote that the comment is due to the result being `bad`.
        """
        type_check(sub_container, (SearchResult, SubtitlesInfo))

        # Get the `SubtitlesInfo` from `SearchResult`, then get subtitle id
        if isinstance(sub_container, SearchResult):
            sub_id_obj = sub_container.subtitles
        sub_id = sub_id_obj.id

        self._request(Endpoints.ADD_COMMENT, sub_id, comment_str, bad)

    def vote(self, sub_container, score):
        """
        Votes for the `sub_id_obj` with a score of `score`.
        """
        type_check(sub_container, (SearchResult, SubtitlesInfo))
        type_check(score, int)

        if score < 1 or score > 10:
            raise ValueError(f"Subtitle Vote must be between 1 and 10, given '{score}'")

        # Get the `SubtitlesInfo` from `SearchResult`, then get subtitle id
        if isinstance(sub_container, SearchResult):
            sub_id_obj = sub_container.subtitles
        sub_id = sub_id_obj.id

        self._request(Endpoints.SUBTITLES_VOTE, sub_id, score)

    def auto_update(self, program_name):
        """
        Returns information about `program_name` that is supposed to be useful for
        automatic updates. (Version info and download urls)
        """
        type_check(program_name, str)

        # Not sure if I should return this information in a better format
        return self._request(Endpoints.AUTO_UPDATE, program_name)

    def preview_subtitles(self, sub_containers):
        """
        Gets a preview for the subtitles represented by `results`. Useful for being able
        to see part of the subtitles without eating into your daily download limit.
        """
        type_check(sub_containers, (list, tuple))

        # Get the subtitles file_ids from `sub_containers`
        file_ids = []
        for sub_container in sub_containers:
            type_check(sub_container, (SearchResult, SubtitlesInfo))
            if isinstance(sub_container, SearchResult):
                sub_container = sub_container.subtitles
            file_ids.append(sub_container.file_id)

        # Batch to 20 per api spec
        return _batch(self._preview_subtitles, 20, [file_ids])

    def _preview_subtitles(self, ids):
        data = self._request(Endpoints.PREVIEW_SUBTITLES, ids)["data"]

        # Unpack our data
        previews = []
        for preview in data:
            encoding = preview["encoding"]
            contents = preview["contents"]

            previews.append(utils.extract(contents, encoding))

        return previews
