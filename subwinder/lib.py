# Endpoints
# * [  ]                   ServerInfo
# * [E?] search_subtitles  SearchSubtitles - pass in (moviehash, size) or tag,
#                              or imdbid, or query
# * [IY] param of ^^       SearchToMail - Have this be a param on above
# * [ Y]                   CheckSubHash - Used for getting tag from the md5
#                              hash, can this get subtitle info from just tag??
# * [E?] search_movie      CheckMovieHash - Useful for getting movie info from
#                              hash
# * [I?] param of ^^       CheckMovieHash2 - May be used in place of ^^
# * [  ] pending           InsertMovieHash - Needs a lot of info, may not be
#                              supported
# * [IN] pending           TryUploadSubtitles - Also needs a lot of info, may
#                              not be supported
# * [EN] pending           UploadSubtitles - Same story as ^^
# * [  ]                   DetectLanguage
# * [  ]                   PreviewSubtitles
# * [E?] download          DownloadSubtitles - Uses idsubfile
# * [E?] report_movie?     ReportWrongMovieHash - Uses idsubfile
# * [E?] pending           ReportWrongImdbMovie - uses movie information for
#                              changing imdb info, look into
# * [EN] get_languages     GetSubLanguages - use this to make sure any language
#                              given is good
# * [  ]                   GetAvailableTranslations
# * [  ]                   GetTranslation
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
# * [  ]                   AutoUpdate

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

import os
import time
from xmlrpc.client import ServerProxy, Transport

from subwinder.constants import _API_BASE, _LANG_2
from subwinder.info import FullUserInfo
from subwinder.exceptions import (
    SubWinderError,
    SubAuthError,
    SubUploadError,
    SubDownloadError,
)


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


# TODO: setup this ranking scheme
def _default_ranking(results):
    pass


class SubWinder:
    # TODO: Move to constants

    _client = ServerProxy(_API_BASE, allow_none=True, transport=Transport())

    def _request(self, method, *params):
        RETRIES = 5
        for _ in range(RETRIES):
            # Flexible way to call method while reducing error handling
            resp = getattr(self._client, method)(*params)

            # All requests are supposed to return a status
            if "status" not in resp:
                # TODO: mention raising an issue
                raise SubWinderError(
                    f'"{method}" should return a status and didn\'t'
                )

            status_code = resp["status"][:3]
            status_msg = resp[4:]

            # Retry if 503, otherwise handle appropriately
            if status_code != "503":
                break

            # Server under heavy load, wait and retry
            time.sleep(1)

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

    # Use limit of searching for 20 different video_paths
    def search_subtitles(
        self, video_paths, ranking=_default_ranking, *rank_params
    ):
        raise NotImplementedError

    def download_subtitles(self, downloads, fmt="{path}/{name}.{lang_3}{ext}"):
        raise NotImplementedError

    def search_movies(self, video_paths, limit=1):
        raise NotImplementedError

    # TODO: use an enum for method?
    def suggest_movie(self, query, method="default"):
        raise NotImplementedError

    def report_movie(self, movie_result):
        raise NotImplementedError

    def get_comments(self, subtitle_result):
        raise NotImplementedError


# TODO: logout on exitting with statement
class AuthSubWinder(SubWinder):
    def __init__(self, useragent, username=None, password=None):
        # Try to get any info from env vars if not passed in
        username = username or os.environ.get("OPEN_SUBTITLES_USERNAME")
        password = password or os.environ.get("OPEN_SUBTITLES_PASSWORD")

        if username is None or password is None:
            raise SubAuthError("username or password is missing")

        if not useragent:
            raise SubAuthError("useragent can not be empty")

        self._token = self._login(useragent, username, password)

    def _request(self, method, *params):
        # These methods don't take auth token
        if method in ("ServerInfo", "LogIn"):
            return super()._request(method, *params)

        # All other methods take the auth token
        return super()._request(method, self._token, *params)

    def _login(self, username, password, useragent):
        resp = self._request("LogIn", username, password, "en", useragent)
        self._token = resp["token"]
        return FullUserInfo(resp["data"])

    def _logout(self):
        self._request("LogOut")

    def user_info(self):
        resp = self._request("GetUserInfo")
        return FullUserInfo(resp["data"])

    def ping(self):
        self._request("NoOperation")

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
#     en_movie_result, es_movie_result = sw.search_movies((movie, "en"),
#                                                         (movie, "es"))
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
