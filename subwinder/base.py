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

from subwinder.info import ServerInfo
from subwinder.lang import lang_2s, lang_3s, lang_longs
from subwinder.request import _request


class Subwinder:
    _token = None

    def __repr__(self):
        return f"{self.__class__.__name__}"

    def _request(self, method, *params):
        # Call the `_request` function with our token
        return _request(method, self._token, *params)

    def daily_download_info(self):
        return self.server_info().daily_download_info

    def get_languages(self):
        return list(zip(lang_2s, lang_3s, lang_longs))

    def server_info(self):
        return ServerInfo.from_data(self._request("ServerInfo"))
