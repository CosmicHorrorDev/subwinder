import pytest

import datetime
import json
import os
from unittest.mock import call, patch

from subwinder.auth import _build_search_query, _default_ranking, AuthSubWinder
from subwinder.exceptions import SubAuthError
from subwinder.info import (
    Comment,
    EpisodeInfo,
    FullUserInfo,
    MovieInfo,
    SubtitlesInfo,
    TvSeriesInfo,
    UserInfo,
)
from subwinder.media import Movie, Subtitles
from subwinder.results import SearchResult
from tests.constants import SAMPLES_DIR


def _dummy_auth_subwinder():
    return AuthSubWinder.__new__(AuthSubWinder)


def _standard_asw_mock(
    method, mocked_method, method_args, response, expected_call, ideal_result
):
    asw = _dummy_auth_subwinder()

    with patch.object(asw, mocked_method, return_value=response) as mocked:
        result = getattr(asw, method)(*method_args)

    mocked.assert_called_with(*expected_call)
    assert result == ideal_result


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


# TODO: mock out the language conversion once getting the languages from the
#       api is implemented
def test__build_search_query():
    # Setup the queries to the intended responses
    PARAM_TO_IDEAL_RESULT = [
        (
            (Movie("0123456789abcdef", 123456), "en"),
            {
                "sublanguageid": "eng",
                "moviehash": "0123456789abcdef",
                "moviebytesize": "123456",
            },
        ),
        (
            (MovieInfo(None, None, "Movie imdbid", None, None), "fr"),
            {"sublanguageid": "fre", "imdbid": "Movie imdbid"},
        ),
        (
            (EpisodeInfo(None, None, "EI imdbid", 1, 2, None, None), "de",),
            {
                "sublanguageid": "ger",
                "imdbid": "EI imdbid",
                "season": 1,
                "episode": 2,
            },
        ),
    ]

    # `assert` that all of the queries get the intended responses
    for args, ideal_result in PARAM_TO_IDEAL_RESULT:
        assert _build_search_query(*args) == ideal_result


# TODO: assert that _request isn't called for bad params?
# TODO: test correct case as well (assert token as well)
def test_authsubwinder__init__():
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
    QUERIES = ("<username>", "<password>", "<useragent>")
    RESP = {"status": "200 OK", "token": "<token>"}
    CALL = ("LogIn", "<username>", "<password>", "en", "<useragent>")

    _standard_asw_mock("_login", "_request", QUERIES, RESP, CALL, "<token>")


def test__logout():
    QUERIES = ()
    RESP = {"status": "200 OK", "seconds": 0.055}
    CALL = ("LogOut",)

    _standard_asw_mock("_logout", "_request", QUERIES, RESP, CALL, None)


def test_check_subtitles():
    QUERIES = (
        [
            Subtitles("a9672c89bc3f5438f820f06bab708067"),
            Subtitles("0ca1f1e42cfb58c1345e149f98ac3aec"),
            Subtitles("11111111111111111111111111111111"),
        ],
    )
    RESP = {
        "status": "200 OK",
        "data": {
            "a9672c89bc3f5438f820f06bab708067": "1",
            "0ca1f1e42cfb58c1345e149f98ac3aec": "3",
            "11111111111111111111111111111111": "0",
        },
        "seconds": "0.009",
    }
    CALL = (
        "CheckSubHash",
        [
            "a9672c89bc3f5438f820f06bab708067",
            "0ca1f1e42cfb58c1345e149f98ac3aec",
            "11111111111111111111111111111111",
        ],
    )
    IDEAL_RESULT = ["1", "3", None]

    _standard_asw_mock(
        "check_subtitles", "_request", QUERIES, RESP, CALL, IDEAL_RESULT
    )


def test_get_comments():
    # Build up the Empty `SearchResult`s and add the `subtitles.id`
    queries = (
        [
            SearchResult.__new__(SearchResult),
            SearchResult.__new__(SearchResult),
        ],
    )
    queries[0][0].subtitles = SubtitlesInfo.__new__(SubtitlesInfo)
    queries[0][0].subtitles.id = "3387112"
    queries[0][1].subtitles = SubtitlesInfo.__new__(SubtitlesInfo)
    queries[0][1].subtitles.id = "3385570"
    with open(os.path.join(SAMPLES_DIR, "get_comments.json")) as f:
        RESP = json.load(f)
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
    CALL = ("GetComments", ["3387112", "3385570"])

    _standard_asw_mock(
        "get_comments", "_request", queries, RESP, CALL, ideal_result
    )


# TODO: split up testing `guess_media` and `_guess_media`
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
    RESP = {"status": "200 OK", "seconds": "0.055"}
    CALL = ("NoOperation",)

    _standard_asw_mock("ping", "_request", (), RESP, CALL, None)


def test_user_info():
    RESP = {
        "status": "200 OK",
        "data": {
            "IDUser": "6",
            "UserNickName": "os",
            "UserRank": "super admin",
            "UploadCnt": "296",
            "UserPreferedLanguages": "cze,eng,slo,tha",
            "DownloadCnt": "1215",
            "UserWebLanguage": "en",
        },
        "seconds": "0.241",
    }
    CALL = ("GetUserInfo",)
    # TODO: switching this out to `from_data` would make it simpler
    ideal_result = FullUserInfo.__new__(FullUserInfo)
    ideal_result.id = "6"
    ideal_result.nickname = "os"
    ideal_result.rank = "super admin"
    ideal_result.uploads = 296
    ideal_result.downloads = 1215
    ideal_result.preferred_languages = ["cze", "eng", "slo", "tha"]
    ideal_result.web_language = "en"

    _standard_asw_mock("user_info", "_request", (), RESP, CALL, ideal_result)
