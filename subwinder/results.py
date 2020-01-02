from dataclasses import dataclass
from datetime import datetime

from subwinder.constants import _TIME_FORMAT
from subwinder.info import (
    SubtitlesInfo,
    UserInfo,
    build_media_info,
)
from subwinder.utils import auto_repr


# TODO: Yeahhhhhh, this class is only holding one thing, may not be worth it
@dataclass
class SubtitlesResult:
    file_id: int


@auto_repr
class SearchResult:
    def __init__(self, data, dirname=None, filename=None):
        # TODO: why is `get` used here, is there a situation where there's no
        #       "UserID"
        if data.get("UserID") == "0":
            self.author = None
        else:
            self.author = UserInfo(data.get("UserID"), data["UserNickName"])

        self.media = build_media_info(data, dirname, filename)
        self.subtitles = SubtitlesInfo(data)
        self.upload_date = datetime.strptime(data["SubAddDate"], _TIME_FORMAT)
