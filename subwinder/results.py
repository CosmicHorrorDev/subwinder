from dataclasses import dataclass
from datetime import datetime

from subwinder.info import (
    EpisodeInfo,
    MovieInfo,
    SubtitlesInfo,
    UserInfo,
    build_media_info,
)
from subwinder.constants import _TIME_FORMAT


# TODO: Yeahhhhhh, this class is only holding one thing, may not be worth it
@dataclass
class SubtitlesResult:
    file_id: int


# TODO: Rename to `SearchResult`?
class SearchResult:
    def __init__(self, data):
        self.author = UserInfo(data.get("UserID"), data["UserNickName"])
        self.media = build_media_info(data)
        self.subtitles = SubtitlesInfo(data)
        self.date = datetime.strptime(data["SubAddDate"], _TIME_FORMAT)
