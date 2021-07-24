from __future__ import annotations

# Optional dependency: atomic_downloads
try:
    from atomicwrites import atomic_write

    ATOMIC_DOWNLOADS_SUPPORT: bool = True
except ImportError:
    ATOMIC_DOWNLOADS_SUPPORT: bool = False


import hashlib
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Callable, Iterable, List, Optional, Tuple, Union, cast

# See: https://github.com/LovecraftianHorror/subwinder/issues/52#issuecomment-637333960
# if you want to know why `request` isn't imported with `from`
import subwinder._request
from subwinder import utils
from subwinder._constants import DEV_USERAGENT, Env
from subwinder._internal_utils import type_check
from subwinder._request import Endpoint
from subwinder.exceptions import (
    SubAuthError,
    SubDownloadError,
    SubLangError,
    SubLibError,
)
from subwinder.info import (
    Comment,
    DownloadInfo,
    Episode,
    FullUser,
    GuessMediaResult,
    Movie,
    SearchResult,
    ServerInfo,
    Subtitles,
    TvSeries,
    build_media,
)
from subwinder.lang import LangFormat, lang_2s, lang_3s, lang_longs
from subwinder.media import MediaFile
from subwinder.names import BaseNameFormatter, NameFormatter
from subwinder.ranking import rank_guess_media, rank_search_subtitles
from subwinder.types import ApiDict, Searchable, SearchQuery, SubContainer, Token


def _build_search_query(query: Searchable, lang: str) -> ApiDict:
    """
    Helper function for `AuthSubwinder.search_subtitles(...)` that handles converting
    the `query` to the appropriate `dict` of information for the API.
    """
    # All queries take a language
    internal_query = {"sublanguageid": lang_2s.convert(lang, LangFormat.LANG_3)}

    # Handle all the different formats for seaching for subtitles
    if isinstance(query, MediaFile):
        # Search by `MediaFile`s hash and size
        internal_query["moviehash"] = query.hash
        internal_query["moviebytesize"] = str(query.size)
    elif isinstance(query, (Movie, Episode)):
        # All `Media` classes provide an `imdbid`
        internal_query["imdbid"] = query.imdbid

        # `Episode` also needs a `season` and `episode`
        if isinstance(query, Episode):
            internal_query["season"] = query.season
            internal_query["episode"] = query.episode
    else:
        raise ValueError(f"`_build_search_query` does not take type of '{type(query)}'")

    return internal_query


def _batch(
    function: Callable,
    batch_size: int,
    iterables: Sequence[Sequence[Any]],
    *args: Any,
    **kwargs: Any,
) -> List[Any]:
    """
    Helper function that batches calls of `function` with at most `batch_size` amount of
    `iterables` each call. Both `args` and `kwargs` will be passed in directly.
    """
    results: List[Any] = []
    for i in range(0, len(iterables[0]), batch_size):
        chunked: List[Any] = []
        for iterable in iterables:
            chunked.append(iterable[i : i + batch_size])

        result: List[Any] = function(*chunked, *args, **kwargs)
        if result is not None:
            results += result

    return results


class Subwinder:
    """
    The class used for all unauthenticated functionality exposed by the library.
    """

    _token: Optional[Token] = None

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def _request(self, endpoint: Endpoint, *params: Any) -> ApiDict:
        """
        Call the API `Endpoint` represented by `method` with any of the given `params`.
        """
        # Call the `request` function with our token
        return subwinder._request.request(endpoint, self._token, *params)

    def daily_download_info(self) -> DownloadInfo:
        """
        Returns `DownloadInfo` for the current client.
        """
        return self.server_info().daily_download_info

    def get_languages(self) -> List[Tuple[str, str, str]]:
        """
        Gets a list of the supported languages for the API in their various formats.
        """
        return list(zip(lang_2s, lang_3s, lang_longs))

    def server_info(self) -> ServerInfo:
        """
        Returns `ServerInfo` for the opensubtitles.
        """
        return ServerInfo.from_data(self._request(Endpoint.SERVER_INFO))


class AuthSubwinder(Subwinder):
    """
    The class used for all authenticated and unauthenticated functionality exposed by
    the library.
    """

    limited_search_size: bool

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        password_hash: Optional[str] = None,
        useragent: Optional[str] = None,
    ) -> None:
        """
        Signs in the user with the given `username`, `password` and program's
        `useragent`. These can also be set as environment variables instead if that's
        preferable. If the parameter is passed in and the env var is set then the
        parameter is used.
        """
        # Try to get any info from env vars if not passed in
        useragent = os.environ.get(Env.USERAGENT.value) or useragent
        username = os.environ.get(Env.USERNAME.value) or username
        password = os.environ.get(Env.PASSWORD.value) or password
        password_hash = os.environ.get(Env.PASSWORD_HASH.value) or password_hash

        # TODO: these SubAuthErrors should really be TypeErrors or ValueErrors
        if password_hash is not None and password is not None:
            raise SubAuthError(
                "`password` and `password_hash` are mutually exclusive. Only one or the"
                " other should be set"
            )

        # Send the password as an md5 hash
        if password is not None:
            password_hash = hashlib.md5(password.encode("UTF-8")).hexdigest()

        self.limited_search_size = False
        if useragent is None or useragent == DEV_USERAGENT:
            # TODO: warn on this once logging is setup
            useragent = DEV_USERAGENT
            self.limited_search_size = True

        if username is None:
            raise SubAuthError(
                "missing `username`, set when initializing `AuthSubwinder` or with the"
                f" {Env.USERNAME.value} env var"
            )

        if password_hash is None:
            raise SubAuthError(
                "missing password hash, this can be set from either password or"
                " password_hash when initializing `AuthSubwinder` or by setting either"
                f" the {Env.PASSWORD.value} or {Env.PASSWORD_HASH.value} env var"
            )

        self._token = self._login(username, password_hash, useragent)

    def __enter__(self) -> AuthSubwinder:
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Logout on exiting `with` if all is well
        if exc_type is None:
            self._logout()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(_token: {repr(self._token)})"

    def _login(self, username: str, password: str, useragent: str) -> Token:
        """
        Handles logging in the user with the provided information and storing the auth
        token. Automatically called by `__init__` so no need to call it directly.
        """
        resp = self._request(Endpoint.LOG_IN, username, password, "en", useragent)
        return Token(resp["token"])

    def _logout(self) -> None:
        """
        Attempts to log out the user from the current session. Automatically called on
        exiting `with` so no need to call it directly.
        """
        self._request(Endpoint.LOG_OUT)
        self._token = None

    def download_subtitles(
        self,
        downloads: Sequence[SubContainer],
        download_dir: Optional[Union[str, Path]] = None,
        name_formatter: BaseNameFormatter = NameFormatter("{upload_filename}"),
    ) -> List[Path]:
        """
        Attempts to download the `SearchResult`s passed in as `downloads`. The download
        will attempt to place files in the same directory as the original file unless
        `download_dir` is provided. Files are automatically named according to the
        provided `name_format`.
        """
        type_check(downloads, (list, tuple))

        sub_containers = []
        download_paths = []
        for download in downloads:
            # All downloads should be some container for `Subtitles`
            type_check(download, (SearchResult, Subtitles))

            if isinstance(download, SearchResult):
                # `SearchResult` holds more info than `Subtitles`
                subtitles = download.subtitles
                media_dirname = download.media.get_dirname()
                media_filename = download.media.get_filename()
            else:
                subtitles = cast(Subtitles, download)
                media_dirname = None
                media_filename = None

            sub_containers.append(subtitles)

            download_paths.append(
                name_formatter.generate(
                    subtitles, media_filename, media_dirname, download_dir
                )
            )

        # TODO: don't need to do this if there's nothing to download
        # Check that the user has enough downloads remaining to satisfy all `downloads`
        daily_remaining = self.daily_download_info().remaining
        if daily_remaining < len(downloads):
            raise SubDownloadError(
                f"Not enough daily downloads remaining ({daily_remaining} <"
                f" {len(downloads)})"
            )

        # Download the subtitles in batches of 20, per api spec
        _batch(self._download_subtitles, 20, [sub_containers, download_paths])

        # Return the list of paths where subtitle files were saved
        return download_paths

    def _download_subtitles(
        self, sub_containers: List[Subtitles], filepaths: List[Path]
    ) -> None:
        sub_file_ids = []
        # Get all the file ids
        sub_file_ids = [sub_container.file_id for sub_container in sub_containers]

        data = self._request(Endpoint.DOWNLOAD_SUBTITLES, sub_file_ids)["data"]

        for result, fpath in zip(data, filepaths):
            subtitles = utils.extract(result["data"])

            # Create the directories if needed, then save the file
            dirpath = fpath.parent
            dirpath.mkdir(exist_ok=True)

            # Write atomically if possible, otherwise fall back to regular writing
            if ATOMIC_DOWNLOADS_SUPPORT:
                with atomic_write(fpath, mode="wb") as f:
                    f.write(subtitles)
            else:
                with fpath.open("wb") as f:
                    f.write(subtitles)

    def get_comments(self, sub_containers: Sequence[SubContainer]) -> List[Comment]:
        """
        Get all `Comment`s for the provided `search_results` if there are any.
        """
        type_check(sub_containers, (list, tuple))

        ids = []
        for sub_container in sub_containers:
            type_check(sub_container, (SearchResult, Subtitles))

            if isinstance(sub_container, SearchResult):
                sub_container = sub_container.subtitles
            ids.append(sub_container.id)
        data = self._request(Endpoint.GET_COMMENTS, ids)["data"]

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

    def user_info(self) -> FullUser:
        """
        Get information stored for the current user.
        """
        return FullUser.from_data(self._request(Endpoint.GET_USER_INFO)["data"])

    def ping(self) -> None:
        """
        Pings the API to keep the session active. Sessions will automatically end after
        15 minutes of inactivity so this can be used to keep a session alive if there's
        no meaningful work to do.
        """
        self._request(Endpoint.NO_OPERATION)

    def guess_media(
        self,
        queries: Sequence[str],
        ranking_func: Callable = rank_guess_media,
        *rank_args: Any,
        **rank_kwargs: Any,
    ) -> List[Union[Movie, TvSeries]]:
        """
        Same as `guess_media_unranked`, but selects the best result using `ranking_func`
        """
        results = self.guess_media_unranked(queries)

        selected = []
        for result, query in zip(results, queries):
            selected.append(ranking_func(result, query, *rank_args, **rank_kwargs))

        return selected

    # TODO: type check the elements of `queries`
    def guess_media_unranked(self, queries: Sequence[str]) -> List[GuessMediaResult]:
        """
        Attempts to guess the media described by each of the `queries`. A custom ranking
        function can be provided to better match the result with `ranking_func` where
        parameters can be passed to this function using `*args` and `**kwargs`.
        """
        type_check(queries, (list, tuple))
        queries = list(queries)

        for query in queries:
            type_check(query, str)

        # Batch to 3 per api spec
        return _batch(self._guess_media_unranked, 3, [queries])

    def _guess_media_unranked(self, queries: List[str]) -> List[GuessMediaResult]:
        data = self._request(Endpoint.GUESS_MOVIE_FROM_STRING, queries)["data"]

        # Special case: `""` is just silently excluded from the response so force it
        if "" in queries and "" not in data:
            data[""] = {}

        # Convert the raw results to `GuessMediaResult`
        return [GuessMediaResult.from_data(data[query]) for query in queries]

    # TODO: can we ensure that the `search_result` was matched using a file hash before
    #       calling this endpoint
    #       And the anser is yes. There are some attributes that only exist on an exact
    #       match
    def report_media(self, sub_container: SubContainer) -> None:
        """
        Reports the subtitles tied to the `search_result`. This can only be done if the
        match was done using a `MediaFile` object so that the subtitles can be tied to a
        specific file. There's a number of good situations to use this like if the
        subtitles were listed under the wrong language, are for the wrong movie, or
        aren't in sync. If theyre OK, but have lots of mistakes or something then it
        would be better to add a comment instead to give context as to why they're bad
        (`.add_comment("<meaningful-comment>", bad=True)`).
        """
        type_check(sub_container, (SearchResult, Subtitles))

        # Get subtitles file_id from `sub_container`
        if isinstance(sub_container, SearchResult):
            sub_container = sub_container.subtitles
        sub_to_movie_id = sub_container.sub_to_movie_id

        # This endpoint should only be used when the subtitles were matched by hash
        if sub_to_movie_id is None:
            raise ValueError(
                "`report_media` can only be called if the subtitles were matched off a"
                " search using a media files hash and size (This is done automatically"
                " when searching with a `MediaFile` object)."
            )

        self._request(Endpoint.REPORT_WRONG_MOVIE_HASH, sub_to_movie_id)

    def search_subtitles(
        self,
        queries: Iterable[SearchQuery],
        ranking_func: Callable = rank_search_subtitles,
        *rank_args: Any,
        **rank_kwargs: Any,
    ) -> List[Optional[SearchResult]]:
        """
        Same as `search_subtitles_unranked`, but the results are run through the
        `ranking_func` first to try and determine the best result.
        """

        # Expand out any possible iterables (like `zip`) to a full list so that they can
        # be checked and batched
        queries = list(queries)

        # Get all the results for the query
        groups = self.search_subtitles_unranked(queries)

        # And select the best results with the `ranking_func`
        selected = []
        for group, (query, _) in zip(groups, queries):
            selected.append(ranking_func(group, query, *rank_args, **rank_kwargs))

        return selected

    def search_subtitles_unranked(
        self, queries: Sequence[SearchQuery]
    ) -> List[List[SearchResult]]:
        """
        Searches for any subtitles that match the provided `queries`. Queries are
        allowed to be `MediaFile`, `Movie`, or `Episode` objects. A custom ranking
        function for matching a result can be provided through `ranking_func` which
        also gets passed the provided `*args` and `**kwargs`.
        """
        # Verify that all the queries are correct before doing any requests
        type_check(queries, (list, tuple, zip))

        # Expand out the `zip` to a `list`
        if isinstance(queries, zip):
            queries = list(queries)

        VALID_CLASSES = (MediaFile, Movie, Episode)
        for query_pair in queries:
            if not isinstance(query_pair, (list, tuple)) or len(query_pair) != 2:
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

        # The API limits to 5 results if the dev useragent is given so only search one
        # item at a time. Otherwise use 20 since there should be plenty of options from
        # the up to 500 results returned
        if self.limited_search_size:
            batch_size = 1
        else:
            batch_size = 20

        return _batch(
            self._search_subtitles_unranked,
            batch_size,
            [queries],
        )

    def _search_subtitles_unranked(
        self, queries: Sequence[SearchQuery]
    ) -> List[List[SearchResult]]:
        internal_queries = [_build_search_query(q, l) for q, l in queries]
        data = self._request(Endpoint.SEARCH_SUBTITLES, internal_queries)["data"]

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

    def suggest_media(self, query: str) -> List[Union[Movie, TvSeries]]:
        """
        Suggest results for guesses of what media is described by `query`.
        """
        type_check(query, str)

        data = self._request(Endpoint.SUGGEST_MOVIE, query)["data"]

        # `data` is an empty list if there were no results
        return [] if not data else [build_media(media) for media in data[query]]

    def add_comment(
        self, sub_container: SubContainer, comment_str: str, bad: bool = False
    ) -> None:
        """
        Adds the comment `comment_str` for the `search_result`. If desired you can
        denote that the comment is due to the result being `bad`.
        """
        type_check(sub_container, (SearchResult, Subtitles))

        # Get the `Subtitles` from `SearchResult`, then get subtitle id
        if isinstance(sub_container, SearchResult):
            sub_container = sub_container.subtitles
        sub_id = sub_container.id

        self._request(Endpoint.ADD_COMMENT, sub_id, comment_str, bad)

    def vote(self, sub_container: SubContainer, score: int) -> None:
        """
        Votes for the `sub_id_obj` with a score of `score`.
        """
        type_check(sub_container, (SearchResult, Subtitles))
        type_check(score, int)

        if score < 1 or score > 10:
            raise ValueError(f"Subtitle Vote must be between 1 and 10, given '{score}'")

        # Get the `Subtitles` from `SearchResult`, then get subtitle id
        if isinstance(sub_container, SearchResult):
            sub_container = sub_container.subtitles
        sub_id = sub_container.id

        self._request(Endpoint.SUBTITLES_VOTE, sub_id, score)

    def auto_update(self, program_name: str) -> Optional[ApiDict]:
        """
        Returns information about `program_name` that is supposed to be useful for
        automatic updates. (Version info and download urls)
        """
        type_check(program_name, str)

        try:
            # Not sure if I should return this information in a better format
            return self._request(Endpoint.AUTO_UPDATE, program_name)
        except SubLibError:
            # No matching program name is returned as "invalid parameters"
            return None

    def preview_subtitles(self, sub_containers: Sequence[SubContainer]) -> List[str]:
        """
        Gets a preview for the subtitles represented by `results`. Useful for being able
        to see part of the subtitles without eating into your daily download limit.
        """
        type_check(sub_containers, (list, tuple))

        # Get the subtitles file_ids from `sub_containers`
        file_ids = []
        for sub_container in sub_containers:
            type_check(sub_container, (SearchResult, Subtitles))
            if isinstance(sub_container, SearchResult):
                sub_container = sub_container.subtitles
            file_ids.append(sub_container.file_id)

        # Batch to 20 per api spec
        return _batch(self._preview_subtitles, 20, [file_ids])

    def _preview_subtitles(self, ids: List[str]) -> List[str]:
        data = self._request(Endpoint.PREVIEW_SUBTITLES, ids)["data"]

        # Unpack our data
        previews = []
        for preview in data:
            encoding = preview["encoding"]
            contents = preview["contents"]

            # Extract and decode the previews
            previews.append(utils.extract(contents).decode(encoding))

        return previews
