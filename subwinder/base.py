from subwinder.info import ServerInfo
from subwinder.lang import lang_2s, lang_3s, lang_longs
from subwinder._request import request


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
        return ServerInfo.from_data(self._request("ServerInfo"))
