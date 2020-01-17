from dataclasses import dataclass
from datetime import datetime

from subwinder.constants import _TIME_FORMAT
from subwinder.lang import LangFormat, lang_3s


# Build the right info object from the "MovieKind"
def build_media_info(data, dirname=None, filename=None):
    MEDIA_MAP = {
        "movie": MovieInfo,
        "episode": EpisodeInfo,
        "tv series": TvSeriesInfo,
    }

    kind = data["MovieKind"]
    if kind in MEDIA_MAP:
        return MEDIA_MAP[kind].from_data(data, dirname, filename)

    # TODO: switch to a sub based error
    raise Exception(f"Undefined MovieKind {data['MovieKind']}")


@dataclass
class UserInfo:
    id: str
    name: str


@dataclass
class FullUserInfo(UserInfo):
    rank: str
    num_uploads: int
    num_downloads: int
    preferred_languages: list
    web_language: str

    def __init__(self, data):
        super().__init__(data["IDUser"], data["UserNickName"])
        self.rank = data["UserRank"]
        self.num_uploads = int(data["UploadCnt"])
        self.num_downloads = int(data["DownloadCnt"])

        # Get all of the languages in 2 char lang
        langs = []
        for lang in data["UserPreferedLanguages"].split(","):
            # Ignore empty string in case of no preferred languages
            if lang:
                langs.append(lang_3s.convert(lang, LangFormat.LANG_2))
        self.preferred_languages = langs

        self.web_language = data["UserWebLanguage"]


@dataclass
class Comment:
    author: UserInfo
    date: datetime
    text: str

    @classmethod
    def from_data(cls, data):
        author = UserInfo(data["UserID"], data["UserNickName"])
        date = datetime.strptime(data["Created"], _TIME_FORMAT)
        text = data["Comment"]

        return cls(author, date, text)


@dataclass
class MediaInfo:
    name: str
    year: int
    imdbid: str
    dirname: str
    filename: str

    @classmethod
    def from_data(cls, data, dirname, filename):
        name = data["MovieName"]
        year = int(data["MovieYear"])
        # For some reason opensubtitles sometimes returns this as an integer
        # Example: best guess when using `guess_media` for "the expanse" has
        #          `type(data["IDMovieIMDB"]) == int`
        imdbid = str(data.get("IDMovieImdb") or data["IDMovieIMDB"])

        return cls(name, year, imdbid, dirname, filename)


class MovieInfo(MediaInfo):
    pass


class TvSeriesInfo(MediaInfo):
    pass


@dataclass
class EpisodeInfo(TvSeriesInfo):
    season: int
    episode: int

    @classmethod
    def from_data(cls, data, dirname, filename):
        tv_series = TvSeriesInfo.from_data(data, dirname, filename)
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
            tv_series.dirname,
            tv_series.filename,
            season,
            episode,
        )


@dataclass
class SubtitlesInfo:
    size: int
    num_downloads: int
    num_comments: int
    rating: float
    id: str
    file_id: str
    sub_to_movie_id: str
    filename: str
    lang_2: str
    lang_3: str
    ext: str
    encoding: str

    @classmethod
    def from_data(cls, data):
        return cls(
            int(data["SubSize"]),
            int(data["SubDownloadsCnt"]),
            int(data["SubComments"]),
            # 0.0 is the listed rating if there are no ratings yet which
            # seems deceptive from a glance
            None if data["SubRating"] == "0.0" else float(data["SubRating"]),
            data["IDSubtitle"],
            data["IDSubtitleFile"],
            # If the search was done with anything other than movie hash and
            # size then there isn't a "IDSubMovieFile"
            None if data["IDSubMovieFile"] == "0" else data["IDSubMovieFile"],
            data["SubFileName"],
            data["ISO639"],
            data["SubLanguageID"],
            data["SubFormat"].lower(),
            data["SubEncoding"],
        )
