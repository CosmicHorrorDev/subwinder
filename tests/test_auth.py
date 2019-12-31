import pytest

import json
import os
from unittest.mock import call, patch

from subwinder.auth import AuthSubWinder
from subwinder.exceptions import SubAuthError
from subwinder.info import TvSeriesInfo, MovieInfo
from tests.constants import SAMPLES_DIR


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


def _dummy_auth_subwinder():
    asw = AuthSubWinder.__new__(AuthSubWinder)
    asw._token = "<token>"

    return asw
