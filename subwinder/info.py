from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from subwinder._constants import TIME_FORMAT
from subwinder.exceptions import SubLibError
from subwinder.lang import LangFormat, lang_3s


# Build the right info object from the "MovieKind"
def build_media_info(data, dirname=None, filename=None):
    """
    Automatically builds `data` into the correct `MediaInfo` class. `dirname` and
    `filename` can be set to tie the resulting object to some local file.
    """
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
    """
    Data container holding basic user information.
    """

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
    """
    Data container holding extensive user information.
    """

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
    """
    Data container for a comment.
    """

    author: UserInfo
    date: datetime
    text: str

    @classmethod
    def from_data(cls, data):
        author = UserInfo.from_data(data)
        date = datetime.strptime(data["Created"], TIME_FORMAT)
        text = data["Comment"]

        return cls(author, date, text)


@dataclass
class MediaInfo:
    """
    Data container for a generic Media.
    """

    name: str
    year: int
    imdbid: str
    dirname: Path
    filename: Path

    @classmethod
    def from_data(cls, data, dirname=None, filename=None):
        name = data["MovieName"]
        year = int(data["MovieYear"])
        # For some reason opensubtitles sometimes returns this as an integer
        # Example: best guess when using `guess_media` for "the expanse" has
        #          `type(data["IDMovieIMDB"]) == int`
        imdbid = str(data.get("IDMovieImdb") or data["IDMovieIMDB"])

        if dirname is not None:
            dirname = Path(dirname)

        if filename is not None:
            filename = Path(filename)

        return cls(name, year, imdbid, dirname, filename)

    def set_filepath(self, filepath):
        filepath = Path(filepath)
        self.set_dirname(filepath.parent)
        self.set_filename(filepath.name)

    def set_filename(self, filename):
        self.filename = Path(filename)

    def set_dirname(self, dirname):
        self.dirname = Path(dirname)


class MovieInfo(MediaInfo):
    """
    Data container for a Movie.
    """


class TvSeriesInfo(MediaInfo):
    """
    Data container for a TV Series.
    """


@dataclass
class EpisodeInfo(TvSeriesInfo):
    """
    Data contianer for a single TV Series Episode.
    """

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
            name=tv_series.name,
            year=tv_series.year,
            imdbid=tv_series.imdbid,
            dirname=tv_series.dirname,
            filename=tv_series.filename,
            season=season,
            episode=episode,
        )


# TODO: are "global_24h_download_limit" and "client_24h_download_limit" ever different?
@dataclass
class DownloadInfo:
    """
    Data container for a user's daily download information.
    """

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
    """
    Data container for various information for opensubtitles' server.
    """

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
    """
    Data container for a set of uploaded Subtitles.
    """

    size: int
    num_downloads: int
    num_comments: int
    rating: float
    id: str
    file_id: str
    sub_to_movie_id: str
    filename: Path
    lang_2: str
    lang_3: str
    ext: str
    encoding: str

    @classmethod
    def from_data(cls, data):
        if data["IDSubMovieFile"] == "0":
            sub_to_movie_id = None
        else:
            sub_to_movie_id = data["IDSubMovieFile"]

        return cls(
            size=int(data["SubSize"]),
            num_downloads=int(data["SubDownloadsCnt"]),
            num_comments=int(data["SubComments"]),
            # 0.0 is the listed rating if there are no ratings yet which seems deceptive
            # at a glance
            rating=None if data["SubRating"] == "0.0" else float(data["SubRating"]),
            id=data["IDSubtitle"],
            file_id=data["IDSubtitleFile"],
            # If the search was done with anything other than movie hash and size then
            # there isn't a "IDSubMovieFile"
            sub_to_movie_id=sub_to_movie_id,
            filename=Path(data["SubFileName"]),
            lang_2=data["ISO639"],
            lang_3=data["SubLanguageID"],
            ext=data["SubFormat"].lower(),
            encoding=data["SubEncoding"],
        )


@dataclass
class SearchResult:
    """
    Data container for a search result from searching for subtitles.
    """

    author: UserInfo
    media: MediaInfo
    subtitles: SubtitlesInfo
    upload_date: datetime

    @classmethod
    def from_data(cls, data, dirname=None, filename=None):
        author = None if data["UserID"] == "0" else UserInfo.from_data(data)
        media = build_media_info(data, dirname, filename)
        subtitles = SubtitlesInfo.from_data(data)
        upload_date = datetime.strptime(data["SubAddDate"], TIME_FORMAT)

        return cls(author, media, subtitles, upload_date)
