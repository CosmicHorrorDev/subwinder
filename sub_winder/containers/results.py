from dataclasses import dataclass
from datetime import datetime

from sub_winder.containers.info import MovieInfo, SubtitlesInfo, UserInfo
from sub_winder.constants import _TIME_FORMAT


# TODO: Yeahhhhhh, this class is only holding one thing, may not be worth it
@dataclass
class SubtitlesResult:
    id: int


class MovieResult:
    def __init__(self, data):
        self.author = UserInfo(data["UserID"], data["UserNickName"])
        if data["MovieKind"] == "movie":
            self.media = MovieInfo(data["MovieName"], data["MovieYear"],
                                   data["IDMovieImdb"])
        else:
            # FIXME: this is just for getting types for debugging
            raise Exception(f"Undefined MovieKind {data['MovieKind']}")
        self.subtitles = SubtitlesInfo(data)
        self.date = datetime.strptime(data["SubAddDate"], _TIME_FORMAT)
