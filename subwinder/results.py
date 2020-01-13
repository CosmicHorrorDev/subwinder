from dataclasses import dataclass
from datetime import datetime

from subwinder.constants import _TIME_FORMAT
from subwinder.info import (
    build_media_info,
    MediaInfo,
    SubtitlesInfo,
    UserInfo,
)


@dataclass
class SearchResult:
    author: UserInfo
    media: MediaInfo
    subtitles: SubtitlesInfo
    upload_date: datetime
    dirname: str = None
    filename: str = None

    @classmethod
    def from_data(cls, data, dirname=None, filename=None):
        if data["UserID"] == "0":
            author = None
        else:
            author = UserInfo(data.get("UserID"), data["UserNickName"])

        media = build_media_info(data, dirname, filename)
        subtitles = SubtitlesInfo.from_data(data)
        upload_date = datetime.strptime(data["SubAddDate"], _TIME_FORMAT)

        return cls(author, media, subtitles, upload_date, dirname, filename)
