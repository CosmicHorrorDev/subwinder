from dataclasses import dataclass
from datetime import datetime

from subwinder.constants import _TIME_FORMAT
from subwinder.info import (
    build_media_info,
    MediaInfo,
    SubtitlesInfo,
    UserInfo,
)


# TODO: Yeahhhhhh, this class is only holding one thing, may not be worth it
@dataclass
class SubtitlesResult:
    file_id: int


# TODO: Some of this data is set to 0 when search was done with imdbid or query
#       (IDSubMovieFile, MovieHash, MovieByteSize, MovieTimeMS will be "0")
@dataclass
class SearchResult:
    author: UserInfo
    media: MediaInfo
    subtitles: SubtitlesInfo
    upload_date: datetime

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
