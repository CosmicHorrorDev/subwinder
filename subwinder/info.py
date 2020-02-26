from dataclasses import dataclass
from datetime import datetime
import os

from subwinder.constants import _TIME_FORMAT
from subwinder.exceptions import SubLibError
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

    raise SubLibError(f"Undefined MovieKind: '{data['MovieKind']}'")


@dataclass
class UserInfo:
    id: str
    name: str

    @classmethod
    def from_data(cls, data):
        return cls(
            # Different keys for the same data again :/
            id=data.get("UserID") or data["IDUser"],
            name=data["UserNickName"],
        )


@dataclass
class FullUserInfo(UserInfo):
    rank: str
    num_uploads: int
    num_downloads: int
    preferred_languages: list
    web_language: str

    @classmethod
    def from_data(cls, data):
        preferred = []
        for lang in data["UserPreferedLanguages"].split(","):
            # Ignore empty string in case of no preferred languages
            if lang:
                preferred.append(lang_3s.convert(lang, LangFormat.LANG_2))

        user_info = UserInfo.from_data(data)

        return cls(
            id=user_info.id,
            name=user_info.name,
            rank=data["UserRank"],
            num_uploads=int(data["UploadCnt"]),
            num_downloads=int(data["DownloadCnt"]),
            preferred_languages=preferred,
            web_language=data["UserWebLanguage"],
        )


@dataclass
class Comment:
    author: UserInfo
    date: datetime
    text: str

    @classmethod
    def from_data(cls, data):
        author = UserInfo.from_data(data)
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

    def set_filepath(self, filepath):
        self.dirname, self.filename = os.path.split(filepath)

    def set_filename(self, filename):
        self.filename = filename

    def set_dirname(self, dirname):
        self.dirname = dirname


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


# TODO: are "global_24h_download_limit" and "client_24h_download_limit" ever different?
@dataclass
class DownloadInfo:
    ip: str
    downloaded: int
    remaining: int
    limit: int
    limit_checked_by: str

    @classmethod
    def from_data(cls, data):
        limits = data["download_limits"]
        return cls(
            ip=limits["client_ip"],
            downloaded=int(limits["client_24h_download_count"]),
            remaining=int(limits["client_download_quota"]),
            limit=int(limits["client_24h_download_limit"]),
            limit_checked_by=limits["limit_check_by"],
        )


@dataclass
class ServerInfo:
    application: str
    users_online: int
    users_logged_in: int
    users_online_peak: int
    users_registered: int
    bots_online: int
    total_subtitles_downloaded: int
    total_subtitle_files: int
    total_movies: int
    daily_download_info: DownloadInfo

    @classmethod
    def from_data(cls, data):
        return cls(
            application=data["application"],
            users_online=int(data["users_online_total"]),
            users_logged_in=int(data["users_loggedin"]),
            users_online_peak=int(data["users_max_alltime"]),
            users_registered=int(data["users_registered"]),
            bots_online=int(data["users_online_program"]),
            total_subtitles_downloaded=int(data["subs_downloads"]),
            total_subtitle_files=int(data["subs_subtitle_files"]),
            total_movies=int(data["movies_total"]),
            daily_download_info=DownloadInfo.from_data(data),
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
            # 0.0 is the listed rating if there are no ratings yet which seems deceptive
            # at a glance
            None if data["SubRating"] == "0.0" else float(data["SubRating"]),
            data["IDSubtitle"],
            data["IDSubtitleFile"],
            # If the search was done with anything other than movie hash and size then
            # there isn't a "IDSubMovieFile"
            None if data["IDSubMovieFile"] == "0" else data["IDSubMovieFile"],
            data["SubFileName"],
            data["ISO639"],
            data["SubLanguageID"],
            data["SubFormat"].lower(),
            data["SubEncoding"],
        )
