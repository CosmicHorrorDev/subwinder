from dataclasses import dataclass
from datetime import datetime

from subwinder.constants import _TIME_FORMAT


class Comment:
    def __init__(self, data):
        self.author = UserInfo(data["UserID"], data["UserNickName"])
        self.created = datetime.strptime(data["Created"], _TIME_FORMAT)
        self.comment_str = data["comment"]


@dataclass
class UserInfo:
    id: str
    nickname: str


class FullUserInfo(UserInfo):
    def __init__(self, data):
        super().__init__(data["IDUser"], data["UserNickName"])
        self.rank = data["UserRank"]
        self.uploads = data["UploadCnt"]
        # FIXME: this is in lang_3 instead of lang_2, convert
        self.prefered_languages = data["UserPreferedLanguages"].split(",")
        self.downloads = data["DownloadCnt"]
        self.web_language = data["UserWebLanguage"]


@dataclass
class MovieInfo:
    name: str
    year: int
    imdbid: str


class SubtitlesInfo:
    def __init__(self, data):
        self.size = int(data["SubSize"])
        self.downloads = int(data["SubDownloadsCnt"])
        self.num_comments = int(data["SubComments"])

        self.rating = float(data["SubRating"])

        self.id = data["IDSubtitle"]
        self.file_id = data["IDSubtitleFile"]
        self.lang_2 = data["ISO639"]
        self.ext = data["SubFormat"]
        self.encoding = data["SubEncoding"]
