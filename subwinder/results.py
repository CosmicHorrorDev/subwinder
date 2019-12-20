from dataclasses import dataclass
from datetime import datetime

# FIXME: handle these warning
from subwinder.info import (
    SubtitlesInfo,
    UserInfo,
    build_media_info,
)
from subwinder.constants import _TIME_FORMAT


# TODO: Yeahhhhhh, this class is only holding one thing, may not be worth it
@dataclass
class SubtitlesResult:
    file_id: int


class SearchResult:
    def __init__(self, data, query):
        if data.get("UserID") == "0":
            self.author = None
        else:
            self.author = UserInfo(data.get("UserID"), data["UserNickName"])

        self.media = build_media_info(data, query)
        self.subtitles = SubtitlesInfo(data)
        self.date = datetime.strptime(data["SubAddDate"], _TIME_FORMAT)
