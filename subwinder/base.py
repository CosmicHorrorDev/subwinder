# Endpoints
# * [??]                   ServerInfo - Can be used to get download limit,
#                              may or may not be supported
# * [IY] search_subtitles param  SearchToMail - Have this be a param on above
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

# TODO: switch to the json api
# TODO: Email the devs about what idsubtitlefile is even used for, related ^^

import time
from xmlrpc.client import ServerProxy, Transport

from subwinder.constants import _API_BASE, _LANG_2, _REPO_URL
from subwinder.exceptions import (
    SubAuthError,
    SubDownloadError,
    SubUploadError,
    SubWinderError,
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
# TODO: would be nice to see headers info, but can't


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
                raise SubWinderError(
                    f'"{method}" should return a status and didn\'t, consider'
                    f" raising an issue at {_REPO_URL}"
                )

            status_code = resp["status"][:3]
            status_msg = resp["status"][4:]

            # Retry if 503, otherwise handle appropriately
            # FIXME: 503 fails the request so it won't be passed in this way
            if status_code != "503":
                break

            # Server under heavy load, wait and retry
            # TODO: exponential backoff till time limit is hit then error?
            time.sleep(1)

        # Handle the response
        if status_code == "200":
            return resp
        elif status_code in _API_ERROR_MAP:
            raise _API_ERROR_MAP[status_code](status_msg)
        else:
            raise SubWinderError(
                "the API returned an unhandled response, consider raising an"
                f" issue to address this at {_REPO_URL}"
                f"\nResp: {status_code}: {status_msg}"
            )

    def get_languages(self):
        return _LANG_2

    def server_info(self):
        # FIXME: return this info in a nicer way?
        # TODO: should we support this method at all?
        return self._request("ServerInfo")

    # TODO: is this even useful?
    #       not likely externally at least
    def search_movies(self, video_paths, limit=1):
        # FIXME: Implement this
        raise NotImplementedError
