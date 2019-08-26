from datetime import datetime

from subwinder.constants import _TIME_FORMAT


class Comment:
    def __init__(self, data):
        self.author = UserInfo(data["UserID"], data["UserNickName"])
        self.created = datetime.strptime(data["Created"], _TIME_FORMAT)
        self.comment_str = data["comment"]


class UserInfo:
    def __init__(self, id, nickname):
        self.id = id
        self.nickname = nickname


class FullUserInfo(UserInfo):
    def __init__(self, data):
        super().__init__(data["IDUser"], data["UserNickName"])
        self.rank = data["UserRank"]
        self.uploads = int(data["UploadCnt"])
        self.downloads = int(data["DownloadCnt"])
        # FIXME: this is in lang_3 instead of lang_2, convert
        self.prefered_languages = data["UserPreferedLanguages"].split(",")
        self.web_language = data["UserWebLanguage"]


class MovieInfo:
    def __init__(self, name, year, imdbid):
        self.name = name
        self.year = int(year)
        self.imdbid = imdbid


class EpisodeInfo(MovieInfo):
    def __init__(self, name, year, imdbid, season_num, episode_num):
        super().__init__(name, year, imdbid)
        self.season_num = int(season_num)
        self.episode_num = int(episode_num)


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
