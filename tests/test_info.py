import pytest

from datetime import datetime
import json
import os
from unittest.mock import patch

from subwinder.info import (
    build_media_info,
    Comment,
    EpisodeInfo,
    FullUserInfo,
    MediaInfo,
    MovieInfo,
    SubtitlesInfo,
    TvSeriesInfo,
    UserInfo,
)
from subwinder.lang import _converter
from tests.constants import (
    EPISODE_INFO1,
    FULL_USER_INFO1,
    USER_INFO1,
    SAMPLES_DIR,
    SUBTITLES_INFO1,
)

# Fake already updated langs to prevent API requests
_converter._langs = [
    ("de", "ger", "German"),
    ("en", "eng", "English"),
    ("fr", "fre", "French"),
]
_converter._last_updated = datetime.now()


def test_build_media_info():
    with open(os.path.join(SAMPLES_DIR, "search_subtitles.json")) as f:
        RESP = json.load(f)
    data = RESP["data"][0]

    # Test detecting the correct type of media
    with patch.object(EpisodeInfo, "from_data") as mocked:
        build_media_info(data)
        mocked.assert_called_once_with(data, None, None)

    data["MovieKind"] = "movie"
    with patch.object(MovieInfo, "from_data") as mocked:
        build_media_info(data)
        mocked.assert_called_once_with(data, None, None)

    data["MovieKind"] = "tv series"
    with patch.object(TvSeriesInfo, "from_data") as mocked:
        build_media_info(data)
        mocked.assert_called_once_with(data, None, None)


def test_UserInfo():
    DATA = {"UserID": "1332962", "UserNickName": "elderman"}

    assert UserInfo.from_data(DATA) == USER_INFO1


def test_FullUserInfo():
    DATA = {
        "UserID": "6",
        "UserNickName": "os",
        "UserRank": "super admin",
        "UploadCnt": "296",
        "DownloadCnt": "1215",
        "UserPreferedLanguages": "ger,eng,fre",
        "UserWebLanguage": "en",
    }

    assert FullUserInfo.from_data(DATA) == FULL_USER_INFO1


def test_Comment():
    DATA = {
        "UserID": "<id>",
        "UserNickName": "<name>",
        "Created": "2000-01-02 03:04:05",
        "Comment": "<comment>",
    }

    assert Comment.from_data(DATA) == Comment(
        UserInfo("<id>", "<name>"), datetime(2000, 1, 2, 3, 4, 5), "<comment>",
    )


def test_MediaInfo():
    DATA = {
        "MovieName": "<name>",
        "MovieYear": "2000",
        "IDMovieImdb": "<imdbid>",
    }

    assert MediaInfo.from_data(DATA, None, None) == MediaInfo(
        "<name>", 2000, "<imdbid>", None, None
    )


@pytest.mark.skip(reason="This isn't any different than `MediaInfo`")
def test_MovieInfo():
    pass


@pytest.mark.skip(reason="This isn't any different than `MediaInfo`")
def test_TvSeriesInfo():
    pass


def test_EpisodeInfo():
    DATA = {
        "MovieName": '"Fringe" Alone in the World',
        "MovieYear": "2011",
        "IDMovieImdb": "1998676",
        "Season": "4",
        "Episode": "3",
    }

    tv_series = TvSeriesInfo.from_data(DATA, None, None)

    assert EpisodeInfo.from_data(DATA, None, None) == EPISODE_INFO1
    assert EpisodeInfo.from_tv_series(tv_series, 4, 3) == EPISODE_INFO1


def test_SubtitlesInfo():
    DATA = {
        "SubSize": "71575",
        "SubDownloadsCnt": "22322",
        "SubComments": "0",
        "SubRating": "0.0",
        "IDSubtitle": "3387112",
        "IDSubtitleFile": "<file-id>",
        "IDSubMovieFile": "0",
        "SubFileName": "sub-filename.sub-ext",
        "ISO639": "<lang-2>",
        "SubLanguageID": "<lang-3>",
        "SubFormat": "<ext>",
        "SubEncoding": "UTF-8",
    }

    assert SubtitlesInfo.from_data(DATA) == SUBTITLES_INFO1
