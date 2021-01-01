import json
from datetime import datetime
from unittest.mock import patch

import pytest

from subwinder.info import (
    Comment,
    Episode,
    FullUser,
    Media,
    Movie,
    SearchResult,
    Subtitles,
    TvSeries,
    User,
    build_media,
)
from tests.constants import (
    EPISODE_INFO1,
    FULL_USER_INFO1,
    SEARCH_RESULT2,
    SUBTITLES_INFO1,
    SUBWINDER_RESPONSES,
    USER_INFO1,
)


def test_build_media_info():
    with (SUBWINDER_RESPONSES / "search_subtitles.json").open() as f:
        RESP = json.load(f)
    data = RESP["data"][0]

    # Test detecting the correct type of media
    with patch.object(Episode, "from_data") as mocked:
        build_media(data)
        mocked.assert_called_once_with(data)

    data["MovieKind"] = "movie"
    with patch.object(Movie, "from_data") as mocked:
        build_media(data)
        mocked.assert_called_once_with(data)

    data["MovieKind"] = "tv series"
    with patch.object(TvSeries, "from_data") as mocked:
        build_media(data)
        mocked.assert_called_once_with(data)


def test_User():
    DATA = {"UserID": "1332962", "UserNickName": "elderman"}

    assert User.from_data(DATA) == USER_INFO1


def test_FullUser():
    with (SUBWINDER_RESPONSES / "full_user_info.json").open() as f:
        DATA = json.load(f)

    assert FullUser.from_data(DATA) == FULL_USER_INFO1


def test_Comment():
    with (SUBWINDER_RESPONSES / "comment.json").open() as f:
        DATA = json.load(f)

    assert Comment.from_data(DATA) == Comment(
        User("<id>", "<name>"),
        datetime(2000, 1, 2, 3, 4, 5),
        "<comment>",
    )


def test_Media():
    with (SUBWINDER_RESPONSES / "media_info.json").open() as f:
        DATA = json.load(f)

    assert Media.from_data(DATA) == Media("<name>", 2000, "<imdbid>", None, None)


@pytest.mark.skip(reason="This isn't any different than `Media`")
def test_Movie():
    pass


@pytest.mark.skip(reason="This isn't any different than `Media`")
def test_TvSeries():
    pass


def test_Episode():
    with (SUBWINDER_RESPONSES / "episode_info.json").open() as f:
        DATA = json.load(f)

    tv_series = TvSeries.from_data(DATA)
    tv_series.set_filepath("/path/to/file.mkv")

    episode_info = Episode.from_data(DATA)
    episode_info.set_filepath("/path/to/file.mkv")

    assert episode_info == EPISODE_INFO1
    assert Episode.from_tv_series(tv_series, 4, 3) == EPISODE_INFO1


def test_Subtitles():
    with (SUBWINDER_RESPONSES / "subtitles_info.json").open() as f:
        DATA = json.load(f)

    assert Subtitles.from_data(DATA) == SUBTITLES_INFO1


def test_SearchResult():
    with (SUBWINDER_RESPONSES / "search_subtitles.json").open() as f:
        SAMPLE_RESP = json.load(f)["data"][0]

    search_result = SearchResult.from_data(SAMPLE_RESP)
    search_result.media.set_filepath("/path/to/file.mkv")
    assert SEARCH_RESULT2 == search_result
