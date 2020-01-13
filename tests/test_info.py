import pytest

from datetime import datetime
import json
import os
from unittest.mock import patch

from subwinder.info import (
    build_media_info,
    Comment,
    EpisodeInfo,
    MediaInfo,
    MovieInfo,
    SubtitlesInfo,
    TvSeriesInfo,
    UserInfo,
)
from tests.constants import SAMPLES_DIR


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
    user = UserInfo("<id>", "<nickname>")
    assert user.id == "<id>"
    assert user.nickname == "<nickname>"


@pytest.mark.skip(reason="Test after implementing `from_data` and `from_user`")
def test_FullUserInfo():
    pass


def test_Comment():
    DATA = {
        "UserID": "<id>",
        "UserNickName": "<nickname>",
        "Created": "2000-01-02 03:04:05",
        "Comment": "<comment>",
    }

    assert Comment.from_data(DATA) == Comment(
        UserInfo("<id>", "<nickname>"),
        datetime(2000, 1, 2, 3, 4, 5),
        "<comment>",
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
        "MovieName": "<name>",
        "MovieYear": "2000",
        "IDMovieImdb": "<imdbid>",
        "Season": "1",
        "Episode": "2",
    }

    tv_series = TvSeriesInfo.from_data(DATA, None, None)
    episode = EpisodeInfo("<name>", 2000, "<imdbid>", None, None, 1, 2)

    assert EpisodeInfo.from_data(DATA, None, None) == episode
    assert EpisodeInfo.from_tv_series(tv_series, 1, 2) == episode


def test_SubtitlesInfo():
    DATA = {
        "SubSize": "1024",
        "SubDownloadsCnt": "100",
        "SubComments": "2",
        "SubRating": "6.0",
        "IDSubtitle": "<id>",
        "IDSubtitleFile": "<id-file>",
        "SubFileName": "<name>",
        "ISO639": "<lang-2>",
        "SubLanguageID": "<lang-3>",
        "SubFormat": "<format>",
        "SubEncoding": "<encoding>",
    }

    assert SubtitlesInfo.from_data(DATA) == SubtitlesInfo(
        1024,
        100,
        2,
        6.0,
        "<id>",
        "<id-file>",
        "<name>",
        "<lang-2>",
        "<lang-3>",
        "<format>",
        "<encoding>",
    )
