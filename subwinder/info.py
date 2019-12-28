from dataclasses import dataclass
from datetime import datetime

from subwinder.constants import _TIME_FORMAT
from subwinder.utils import auto_repr


# Just build the right info object from the "MovieKind"
def build_media_info(data, file_dir=None, file_name=None):
    MEDIA_MAP = {
        "movie": MovieInfo,
        "episode": EpisodeInfo,
        "tv series": TvSeriesInfo,
    }

    kind = data["MovieKind"]
    if kind in MEDIA_MAP:
        return MEDIA_MAP[kind].from_data(data, file_dir, file_name)

    # TODO: switch to a sub based error
    raise Exception(f"Undefined MovieKind {data['MovieKind']}")


@auto_repr
class Comment:
    def __init__(self, data):
        self.author = UserInfo(data["UserID"], data["UserNickName"])
        self.created = datetime.strptime(data["Created"], _TIME_FORMAT)
        self.comment_str = data["Comment"]


@dataclass
class UserInfo:
    id: str
    nickname: str


@auto_repr
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


@dataclass
class MediaInfo:
    name: str
    year: int
    imdbid: str
    file_dir: str
    file_name: str

    @classmethod
    def from_data(cls, data, file_dir, file_name):
        name = data["MovieName"]
        year = int(data["MovieYear"])
        imdbid = data.get("IDMovieImdb") or data["IDMovieIMDB"]

        return cls(name, year, imdbid, file_dir, file_name)


class MovieInfo(MediaInfo):
    pass


class TvSeriesInfo(MediaInfo):
    pass


@auto_repr
class EpisodeInfo(TvSeriesInfo):
    def __init__(
        self, name, year, imdbid, season, episode, file_dir, file_name
    ):
        super().__init__(name, year, imdbid, file_dir, file_name)
        self.season = season
        self.episode = episode

    @classmethod
    def from_data(cls, data, file_dir, file_name):
        tv_series = TvSeriesInfo.from_data(data, file_dir, file_name)
        # Yay different keys for the same data!
        season = int(data.get("SeriesSeason") or data.get("Season"))
        episode = int(data.get("SeriesEpisode") or data.get("Episode"))

        return cls.from_tv_series(tv_series, season, episode)

    @classmethod
    def from_tv_series(cls, tv_series, season, episode):
        return cls(
            tv_series.name,
            tv_series.year,
            tv_series.imdbid,
            season,
            episode,
            tv_series.file_dir,
            tv_series.file_name,
        )


@auto_repr
class SubtitlesInfo:
    def __init__(self, data):
        self.size = int(data["SubSize"])
        self.downloads = int(data["SubDownloadsCnt"])
        self.num_comments = int(data["SubComments"])

        self.rating = float(data["SubRating"])

        self.id = data["IDSubtitle"]
        self.file_id = data["IDSubtitleFile"]

        self.media_filename = data["SubFileName"]
        self.lang_2 = data["ISO639"]
        self.lang_3 = data["SubLanguageID"]
        self.ext = data["SubFormat"].lower()
        self.encoding = data["SubEncoding"]
