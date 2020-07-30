import pytest

from datetime import datetime
import json
from unittest.mock import patch

from subwinder.info import (
    build_media_info,
    Comment,
    EpisodeInfo,
    FullUserInfo,
    MediaInfo,
    MovieInfo,
    SearchResult,
    SubtitlesInfo,
    TvSeriesInfo,
    UserInfo,
)
from tests.constants import (
    EPISODE_INFO1,
    FULL_USER_INFO1,
    USER_INFO1,
    SAMPLES_DIR,
    SEARCH_RESULT2,
    SUBTITLES_INFO1,
)


def test_build_media_info():
    with (SAMPLES_DIR / "search_subtitles.json").open() as f:
        RESP = json.load(f)
    data = RESP["data"][0]

    # Test detecting the correct type of media
    with patch.object(EpisodeInfo, "from_data") as mocked:
        build_media_info(data)
        mocked.assert_called_once_with(data)

    data["MovieKind"] = "movie"
    with patch.object(MovieInfo, "from_data") as mocked:
        build_media_info(data)
        mocked.assert_called_once_with(data)

    data["MovieKind"] = "tv series"
    with patch.object(TvSeriesInfo, "from_data") as mocked:
        build_media_info(data)
        mocked.assert_called_once_with(data)


def test_UserInfo():
    # TODO: Is there any better place to get this information?
    DATA = {"UserID": "1332962", "UserNickName": "elderman"}

    assert UserInfo.from_data(DATA) == USER_INFO1


def test_FullUserInfo():
    # TODO: Is there any better place to get this information?
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
    # TODO: Is there any better place to get this information?
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
    # TODO: Is there any better place to get this information?
    DATA = {
        "MovieName": "<name>",
        "MovieYear": "2000",
        "IDMovieImdb": "<imdbid>",
    }

    assert MediaInfo.from_data(DATA) == MediaInfo(
        "<name>", 2000, "<imdbid>", None, None
    )


@pytest.mark.skip(reason="This isn't any different than `MediaInfo`")
def test_MovieInfo():
    pass


@pytest.mark.skip(reason="This isn't any different than `MediaInfo`")
def test_TvSeriesInfo():
    pass


def test_EpisodeInfo():
    # TODO: Is there any better place to get this information?
    DATA = {
        "MovieName": '"Fringe" Alone in the World',
        "MovieYear": "2011",
        "IDMovieImdb": "1998676",
        "Season": "4",
        "Episode": "3",
    }

    tv_series = TvSeriesInfo.from_data(DATA)
    tv_series.set_filepath("/path/to/file.mkv")

    episode_info = EpisodeInfo.from_data(DATA)
    episode_info.set_filepath("/path/to/file.mkv")

    assert episode_info == EPISODE_INFO1
    assert EpisodeInfo.from_tv_series(tv_series, 4, 3) == EPISODE_INFO1


def test_SubtitlesInfo():
    # TODO: Is there any better place to get this information?
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


def test_SearchResult():
    # XXX: switch this to pathlib style open
    with (SAMPLES_DIR / "search_subtitles.json").open() as f:
        SAMPLE_RESP = json.load(f)["data"][0]

    search_result = SearchResult.from_data(SAMPLE_RESP)
    # XXX: can I get rid of this?
    search_result.media.set_filepath("/path/to/file.mkv")
    assert SEARCH_RESULT2 == search_result
