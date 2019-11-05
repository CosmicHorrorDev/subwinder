# TODO: add `__repr__` to all of these to ease development
from datetime import datetime

from subwinder.constants import _TIME_FORMAT


# Just build the right info object from the "MovieKind"
def build_media_info(data):
    MEDIA_MAP = {
        "movie": MovieInfo,
        "episode": EpisodeInfo,
        "tv series": EpisodeInfo,
    }

    kind = data["MovieKind"]
    if kind in MEDIA_MAP:
        return MEDIA_MAP[kind](data)

    # TODO: switch to a sub based error
    raise Exception(f"Undefined MovieKind {data['MovieKind']}")


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
        preferred_languages = data["UserPreferedLanguages"].split(",")
        self.preferred_languages = [p_l for p_l in preferred_languages if p_l]
        self.web_language = data["UserWebLanguage"]


class MediaInfo:
    def __init__(self, data):
        self.name = data["MovieName"]
        self.year = int(data["MovieYear"])
        self.imdbid = data.get("IDMovieImdb") or data.get("IDMovieIMDB")


class MovieInfo(MediaInfo):
    pass


class EpisodeInfo(MediaInfo):
    def __init__(self, data):
        super().__init__(data)
        # Yay different keys for the same data!
        season = data.get("SeriesSeason") or data.get("Season")
        episode = data.get("SeriesEpisode") or data.get("Episode")
        self.season_num = int(season)
        self.episode_num = int(episode)


class SubtitlesInfo:
    def __init__(self, data):
        self.size = int(data["SubSize"])
        self.downloads = int(data["SubDownloadsCnt"])
        self.num_comments = int(data["SubComments"])

        self.rating = float(data["SubRating"])

        self.id = data["IDSubtitle"]
        self.file_id = data["IDSubtitleFile"]
        self.sub_to_movie_id = data["IDSubMovieFile"]

        self.media_filename = data["SubFileName"]
        self.lang_2 = data["ISO639"]
        self.lang_3 = data["SubLanguageID"]
        self.ext = data["SubFormat"].lower()
        self.encoding = data["SubEncoding"]
