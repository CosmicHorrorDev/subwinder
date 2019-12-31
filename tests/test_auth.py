import pytest

import datetime
import json
import os
from unittest.mock import call, patch

from subwinder.auth import _default_ranking, AuthSubWinder
from subwinder.exceptions import SubAuthError
from subwinder.info import (
    Comment,
    MovieInfo,
    SubtitlesInfo,
    TvSeriesInfo,
    UserInfo,
)
from subwinder.results import SearchResult
from tests.constants import SAMPLES_DIR


def _dummy_auth_subwinder():
    return AuthSubWinder.__new__(AuthSubWinder)


def test__default_ranking():
    DUMMY_RESULTS = [
        {"SubBad": "1", "SubFormat": "ASS", "SubDownloadsCnt": "600"},
        {"SubBad": "0", "SubFormat": "Srt", "SubDownloadsCnt": "500"},
    ]

    # Format is (<args>, <kwargs>, <result>)
    PARAM_TO_IDEAL_RESULT = [
        # Empty results means nothing matched the query
        (([], 0), {}, None),
        # Exludes `DUMMY_RESULTS[0]` because it's _bad_
        ((DUMMY_RESULTS, 0), {}, DUMMY_RESULTS[1]),
        # Prefers `DUMMY_RESULTS[0]` because there's more downloads
        ((DUMMY_RESULTS, 0), {"exclude_bad": False}, DUMMY_RESULTS[0]),
        # Ecludes `DUMMY_RESULTS[0]` because of format
        ((DUMMY_RESULTS, 0), {"sub_exts": ["SRT"]}, DUMMY_RESULTS[1]),
        # What happens when nothing matches the parameters?
        (
            (DUMMY_RESULTS, 0),
            {"exclude_bad": True, "sub_exts": ["ass"]},
            None,
        ),
    ]

    for args, kwargs, ideal_result in PARAM_TO_IDEAL_RESULT:
        assert _default_ranking(*args, **kwargs) == ideal_result


# TODO: assert that _request isn't called for bad params?
# TODO: test correct case as well (assert token as well)
def test_authsubwinder_init():
    bad_params = [
        # Missing both username and password
        ["<useragent"],
        # Missing password
        ["<useragent>", "<username>"],
        # Invalid useragent
        [None, "<username>", "<password>"],
    ]

    for params in bad_params:
        with pytest.raises(SubAuthError):
            AuthSubWinder(*params)


def test__login():
    asw = _dummy_auth_subwinder()

    IDEAL_RESP = {"status": "200 OK", "token": "<token>"}

    with patch.object(asw, "_request", return_value=IDEAL_RESP) as mocked:
        asw._login("<username>", "<password>", "<useragent>")

    mocked.assert_called_with(
        "LogIn", "<username>", "<password>", "en", "<useragent>"
    )


def test__logout():
    asw = _dummy_auth_subwinder()
    # asw._token = "<token>"

    IDEAL_RESP = {"status": "200 OK", "seconds": 0.055}

    with patch.object(asw, "_request", return_value=IDEAL_RESP) as mocked:
        asw._logout()

    mocked.assert_called_with("LogOut")
    # assert asw._token is None


def test_get_comments():
    asw = _dummy_auth_subwinder()

    # Build up the Empty `SearchResult`s and add the `subtitles.id`
    queries = [
        SearchResult.__new__(SearchResult),
        SearchResult.__new__(SearchResult),
    ]
    queries[0].subtitles = SubtitlesInfo.__new__(SubtitlesInfo)
    queries[0].subtitles.id = "3387112"
    queries[1].subtitles = SubtitlesInfo.__new__(SubtitlesInfo)
    queries[1].subtitles.id = "3385570"

    ideal_result = [
        [Comment.__new__(Comment)],
        [Comment.__new__(Comment), Comment.__new__(Comment)],
    ]
    ideal_result[0][0].author = UserInfo("192696", "neo_rtr")
    ideal_result[0][0].created = datetime.datetime(2008, 12, 14, 17, 20, 42)
    ideal_result[0][0].comment_str = "Greate Work. thank you"
    ideal_result[1][0].author = UserInfo("745565", "pee-jay_cz")
    ideal_result[1][0].created = datetime.datetime(2008, 12, 12, 15, 21, 48)
    ideal_result[1][0].comment_str = "Thank you."
    ideal_result[1][1].author = UserInfo("754781", "Guzeppi")
    ideal_result[1][1].created = datetime.datetime(2008, 12, 12, 15, 51, 1)
    ideal_result[1][1].comment_str = "You're welcome :)"
    with open(os.path.join(SAMPLES_DIR, "get_comments.json")) as f:
        SAMPLE_RESP = json.load(f)

    with patch.object(asw, "_request", return_value=SAMPLE_RESP) as mocked:
        comments = asw.get_comments(queries)

    assert comments == ideal_result
    mocked.assert_called_with("GetComments", ["3387112", "3385570"])


def test_guess_media():
    asw = _dummy_auth_subwinder()

    QUERIES = [
        "heross01e08.avi",
        "Insurgent.2015.READNFO.CAM.AAC.x264-LEGi0N",
        "Night Watch",
        "Aliens 1080p BluRay AC3 x264-ETRG.mkv",
    ]
    # The calls are split due to batching
    CALLS = [
        call("GuessMovieFromString", QUERIES[:3]),
        call("GuessMovieFromString", QUERIES[3:]),
    ]
    IDEAL_RESULT = [
        TvSeriesInfo("Heroes", 2006, "0813715", None, None),
        MovieInfo("Insurgent", 2015, "2908446", None, None),
        MovieInfo("Nochnoy dozor", 2004, "0403358", None, None),
        MovieInfo("Aliens", 1986, "0090605", None, None),
    ]
    with open(os.path.join(SAMPLES_DIR, "guess_media.json")) as f:
        SAMPLE_RESP = json.load(f)

    with patch.object(asw, "_request") as mocked:
        mocked.side_effect = SAMPLE_RESP
        guesses = asw.guess_media(QUERIES)

    assert guesses == IDEAL_RESULT
    mocked.assert_has_calls(CALLS)


def test_ping():
    asw = _dummy_auth_subwinder()

    IDEAL_RESP = {"status": "200 OK", "seconds": 0.055}

    with patch.object(asw, "_request", return_value=IDEAL_RESP) as mocked:
        asw.ping()

    mocked.assert_called_with("NoOperation")
