# Endpoints
# * [??]                   ServerInfo - Can be used to get download limit,
#                              may or may not be supported
# * [E?] search_subtitles  SearchSubtitles - pass in (moviehash, size) or tag,
#                              or imdbid, or query
# * [IY] param of ^^       SearchToMail - Have this be a param on above
# * [EY] check_subtitles   CheckSubHash - Used for getting tag from the md5
#                              hash, can this get subtitle info from just tag??
# * [E?] search_movie      CheckMovieHash - Useful for getting movie info from
#                              hash
# * [I?] param of ^^       CheckMovieHash2 - May be used in place of ^^
# * [??] pending           InsertMovieHash - Needs a lot of info, may not be
#                              supported
# * [IN] pending           TryUploadSubtitles - Also needs a lot of info, may
#                              not be supported
# * [EN] pending           UploadSubtitles - Same story as ^^
# * [E?] download          DownloadSubtitles - Uses idsubfile
# * [E?] report_movie?     ReportWrongMovieHash - Uses idsubfile
# * [E?] pending           ReportWrongImdbMovie - uses movie information for
#                              changing imdb info, look into
# * [??] pending           InsertMovie
# * [EY] vote              SubtitlesVote - Uses idsubtitle
# * [E?] get_comments      GetComments - Uses idsubtitle
# * [EY] add_comment       AddComment - Uses idsubtitle
# * [E?] request           AddRequest - uses imdbid
# * [E?] set_subscribe_url SetSubscribeUrl - Just give url
# * [E?] subscribe         SubscribeToHash - Give the moviehash (should check
#                              for movie hash?)
# * [E?] param of vv       QuickSuggest - Just querystring and language
# * [E?] suggest_movie     SuggestMovie - ^^
# * [E?] param of srch_mv? GuessMovieFromString - Just needs the title string,
#                              is slow though

# Hide from user:
# * Any of the hashes and sizes needed
# * Token
# * Logging out
# * IMDBid?
# * IDSubtitle and IDsubfile?
# * Ignore a bunch of things that aren't really used?

# Features:
# * With will login on entry and logout on exit, should raise errors from
#   useragent, bad user/pass, or invalid language tag
# * download_subtitles should download next to movie, auto-batch to max
#     * Nevermind, specify format with the download class?
# * report_movie_hash should take a good_result
# * vote_subtitles should be limited 1 to 10

# TODO: try to switch movie to media in places where it could be a movie or
#       episode

import os
import time
from xmlrpc.client import ServerProxy, Transport

from subwinder.constants import _API_BASE, _LANG_2
from subwinder.info import FullUserInfo, MediaInfo
from subwinder.exceptions import (
    SubWinderError,
    SubAuthError,
    SubUploadError,
    SubDownloadError,
)
from subwinder.results import SearchResult


# Responses 403, 404, 405, 406, 409 should be prevented by API
_API_ERROR_MAP = {
    "401": SubAuthError,
    "402": SubUploadError,
    "407": SubDownloadError,
    "408": SubWinderError,
    "410": SubWinderError,
    "411": SubAuthError,
    "412": SubWinderError,
    "413": SubWinderError,
    "414": SubAuthError,
    "415": SubAuthError,
    "416": SubUploadError,
    "506": SubWinderError,
}


# TODO: include some way to check download limit for this account
#       Info is just included in ServerInfo


# FIXME: rank by highest score?
def _default_ranking(results, query_index, exclude_bad=True, sub_exts=["srt"]):
    best_result = None
    max_downloads = None
    DOWN_KEY = "SubDownloadsCnt"
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


class SubWinder:
    _client = ServerProxy(_API_BASE, allow_none=True, transport=Transport())
    _token = None

    # FIXME: Handle xmlrpc.client.ProtocolError, 503 and 506 are raised as
    #        protocol errors, change to allow for this
    #        Also occurs for 520 which isn't listed
    # TODO: give a way to let lib user to set `RETRIES`?
    # TODO: should it do constant retries or exponential backoff with timeout?
    def _request(self, method, *params):
        RETRIES = 5
        for _ in range(RETRIES):
            if method in ("ServerInfo", "LogIn"):
                # Flexible way to call method while reducing error handling
                resp = getattr(self._client, method)(*params)
            else:
                # Use the token if it's defined
                resp = getattr(self._client, method)(self._token, *params)

            # All requests are supposed to return a status
            # But of course ServerInfo doesn't for no reason
            if method == "ServerInfo":
                return resp

            if "status" not in resp:
                # TODO: mention raising an issue
                raise SubWinderError(
                    f'"{method}" should return a status and didn\'t'
                )

            status_code = resp["status"][:3]
            status_msg = resp["status"][4:]

            # Retry if 503, otherwise handle appropriately
            if status_code != "503":
                break

            # Server under heavy load, wait and retry
            time.sleep(1)

        # FIXME: add handling for 503 exausting all `RETRIES`
        # Handle the response
        if status_code == "200":
            return resp
        elif status_code in _API_ERROR_MAP:
            raise _API_ERROR_MAP[status_code](status_msg)
        else:
            # TODO: mention raising an issue once the github repo is up
            raise SubWinderError("the API returned an unhandled response")

    def get_languages(self):
        return _LANG_2

    def server_info(self):
        # FIXME: return this info in a nicer way?
        # TODO: should we support this method at all?
        return self._request("ServerInfo")

    # TODO: have the downloads be list of pairs for `(SearchResult, path)`?
    def download_subtitles(self, downloads, fmt="{path}/{name}.{lang_3}{ext}"):
        # FIXME: Implement this
        raise NotImplementedError

    def search_movies(self, video_paths, limit=1):
        # FIXME: Implement this
        raise NotImplementedError

    def report_movie(self, movie_result):
        # FIXME: Implement this
        raise NotImplementedError

    def get_comments(self, subtitle_result):
        # FIXME: Implement this
        raise NotImplementedError


class AuthSubWinder(SubWinder):
    def __init__(self, useragent, username=None, password=None):
        # Try to get any info from env vars if not passed in
        username = username or os.environ.get("OPEN_SUBTITLES_USERNAME")
        password = password or os.environ.get("OPEN_SUBTITLES_PASSWORD")

        if username is None or password is None:
            raise SubAuthError("username or password is missing")

        if not useragent:
            raise SubAuthError("useragent can not be empty")

        self._token = self._login(username, password, useragent)

    def _login(self, username, password, useragent):
        resp = self._request("LogIn", username, password, "en", useragent)
        return resp["token"]

    # FIXME: this should be done on exiting `with`
    def _logout(self):
        self._request("LogOut")

    def user_info(self):
        resp = self._request("GetUserInfo")
        return FullUserInfo(resp["data"])

    def ping(self):
        self._request("NoOperation")

    def guess_media(self, queries):
        if isinstance(queries, str):
            queries = (queries,)

        resp = self._request("GuessMovieFromString", queries)
        data = resp["data"]

        # TODO: is there a better return type for this?
        return [MediaInfo(data[q]["BestGuess"]) for q in queries]

    # TODO: Use limit of searching for 20 different video_paths
    # TODO: this takes 3-char language, convert from 2-char internally
    # TODO: see if limiting for each search is possible, looks to be total
    def search_subtitles(
        self, queries, *, ranking_function=_default_ranking, **rank_params
    ):
        internal_queries = []
        for movie, lang in queries:
            internal_queries.append(
                {
                    "sublanguageid": lang,
                    "moviehash": movie.hash,
                    "moviebytesize": movie.size
                }
            )

        data = self._request("SearchSubtitles", internal_queries)["data"]
        groups = [[] for _ in internal_queries]
        # TODO: this is slightly ugly, rethink
        # Go through the results and organize them in the order of `queries`
        for i, query in enumerate(internal_queries):
            for d in data:
                if d["QueryParameters"] == query:
                    groups[i].append(d)

        results = []
        for group, query in zip(groups, queries):
            result = ranking_function(group, query, **rank_params)
            results.append(result)

        return [SearchResult(r) for r in results]

    def suggest_media(self, query):
        resp = self._request("SuggestMovie", query)
        raw_movies = resp["data"][query]

        # TODO: is there a better to set up the class for this?
        return [MediaInfo(r_m) for r_m in raw_movies]

    def add_comment(self, subtitle_result, comment_str, bad=False):
        # TODO: magically get the subtitle id from the result
        self._request("AddComment", subtitle_id, comment_str, bad)


# # Design Goals
# # Setting up our initial `AuthSubWinder` `Movie` and `Subtitles` objects
# with AuthSubWinder("<user-agent>", "<username>", "<password>") as sw:
#     movie = Movie("/path/to/movie.mkv")
#     subs = Subtitles("/path/to/movie.deu.srt")
#
#     # Method that needs both a `Movie` and `Subtitles` object
#     sw.upload_subtitles(movie, subs, ...)
#
#     # Methods that need a `Movie` object
#     sw.subscribe(movie)
#     en_movie_result, es_movie_result = sw.search_movies([(movie, "en"),
#                                                          (movie, "es")])
#     # TODO: how will this give any location information on where to download?
#     sw.download([en_movie_result, es_movie_result])
#
#     # Method that needs just a `SearchResult` object
#     sw.report_wrong_movie(en_movie_result)
#
#     # Method that needs just a `Subtitles` object
#     subs_result = sw.check_subtitles(subs)
#
#     # Methods that could take either a `SearchResult` or `SubtitlesResult`
#     sw.vote(subs_result, 10)
#     sw.add_comment(subs_result, "Subs were great, thanks!")
#     comments = sw.get_comments(en_movie_result)
