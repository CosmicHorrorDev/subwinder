from datetime import datetime as dt
import os

from subwinder.info import (
    EpisodeInfo,
    FullUserInfo,
    MovieInfo,
    SubtitlesInfo,
    UserInfo,
)
from subwinder.media import Media
from subwinder.results import SearchResult


TEST_DIR = os.path.dirname(__file__)
SAMPLES_DIR = os.path.join(TEST_DIR, "sample_responses")

MEDIA1 = Media("18379ac9af039390", 366876694)
USER_INFO1 = UserInfo("1332962", "elderman")

FULL_USER_INFO1 = FullUserInfo(
    id="6",
    name="os",
    rank="super admin",
    num_uploads=296,
    num_downloads=1215,
    preferred_languages=["de", "en", "fr"],
    web_language="en",
)

MOVIE_INFO1 = MovieInfo(
    name="<movie-name>",
    year=2015,
    imdbid="<imdbid>",
    dirname="movie_dir",
    filename="movie_file",
)

EPISODE_INFO1 = EpisodeInfo(
    name='"Fringe" Alone in the World',
    year=2011,
    imdbid="1998676",
    dirname=None,
    filename=None,
    season=4,
    episode=3,
)

SUBTITLES_INFO1 = SubtitlesInfo(
    size=71575,
    num_downloads=22322,
    num_comments=0,
    rating=None,
    id="3387112",
    file_id="<file-id>",
    sub_to_movie_id=None,
    filename="sub-filename.sub-ext",
    lang_2="<lang-2>",
    lang_3="<lang-3>",
    ext="<ext>",
    encoding="UTF-8",
)

SUBTITLES_INFO2 = SubtitlesInfo(
    size=58024,
    num_downloads=57765,
    num_comments=2,
    rating=None,
    id="4251071",
    file_id="1952941557",
    sub_to_movie_id="3585468",
    filename="Fringe.S04E03.HDTV.XviD-LOL.srt",
    lang_2="en",
    lang_3="eng",
    ext="srt",
    encoding="UTF-8",
)

SEARCH_RESULT1 = SearchResult(
    author=None,
    media=MOVIE_INFO1,
    subtitles=SUBTITLES_INFO1,
    upload_date=dt(2015, 3, 29, 13, 23, 44),
)

SEARCH_RESULT2 = SearchResult(
    USER_INFO1, EPISODE_INFO1, SUBTITLES_INFO2, dt(2011, 10, 8, 7, 36, 1),
)
