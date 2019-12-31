import pytest

import json
import os
from unittest.mock import call, patch

from subwinder.auth import _default_ranking, AuthSubWinder
from subwinder.exceptions import SubAuthError
from subwinder.info import TvSeriesInfo, MovieInfo
from tests.constants import SAMPLES_DIR


def test_default_ranking():
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
