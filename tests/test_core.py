import pytest

from datetime import datetime
import json
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import call, patch

from subwinder import AuthSubwinder, Subwinder
from subwinder._request import Endpoints
from subwinder.core import _build_search_query
from subwinder.exceptions import SubAuthError, SubDownloadError
from subwinder.info import (
    Comment,
    MovieInfo,
    TvSeriesInfo,
    UserInfo,
)
from subwinder.lang import _converter
from subwinder.ranking import rank_search_subtitles
from tests.constants import (
    DOWNLOAD_INFO,
    EPISODE_INFO1,
    FULL_USER_INFO1,
    MEDIA1,
    MOVIE_INFO1,
    SAMPLES_DIR,
    SEARCH_RESULT1,
    SEARCH_RESULT2,
    SERVER_INFO,
)


# Fake already updated langs to prevent API requests
_converter._langs = [
    ["de", "en", "fr"],
    ["ger", "eng", "fre"],
    ["German", "English", "French"],
]
_converter._last_updated = datetime.now()


def _dummy_auth_subwinder():
    return AuthSubwinder.__new__(AuthSubwinder)


def _standard_asw_mock(
    method, mocked_method, method_args, response, expected_call, ideal_result
):
    asw = _dummy_auth_subwinder()

    with patch.object(asw, mocked_method, return_value=response) as mocked:
        result = getattr(asw, method)(*method_args)

    mocked.assert_called_with(*expected_call)
    assert result == ideal_result


def test__build_search_query():
    # Setup the queries to the intended responses
    PARAM_TO_IDEAL_RESULT = [
        (
            (MEDIA1, "en"),
            {
                "sublanguageid": "eng",
                "moviehash": str(MEDIA1.hash),
                "moviebytesize": str(MEDIA1.size),
            },
        ),
        ((MOVIE_INFO1, "fr"), {"sublanguageid": "fre", "imdbid": MOVIE_INFO1.imdbid},),
        (
            (EPISODE_INFO1, "de"),
            {
                "sublanguageid": "ger",
                "imdbid": EPISODE_INFO1.imdbid,
                "season": EPISODE_INFO1.season,
                "episode": EPISODE_INFO1.episode,
            },
        ),
    ]

    # `assert` that all of the queries get the intended responses
    for args, ideal_result in PARAM_TO_IDEAL_RESULT:
        assert _build_search_query(*args) == ideal_result


@pytest.mark.skip(reason="Only passes the values onto `_request`")
def test__request():
    pass


def test_daily_download_info():
    with open(SAMPLES_DIR / "server_info.json") as f:
        RESP = json.load(f)
    IDEAL = DOWNLOAD_INFO

    with patch.object(Subwinder, "_request", return_value=RESP) as mocked:
        result = Subwinder().daily_download_info()

    assert result == IDEAL
    mocked.assert_called_once_with(Endpoints.SERVER_INFO)


def test_get_languages():
    sw = Subwinder()
    assert sw.get_languages() == [
        ("de", "ger", "German"),
        ("en", "eng", "English"),
        ("fr", "fre", "French"),
    ]


def test_server_info():
    with open(SAMPLES_DIR / "server_info.json") as f:
        RESP = json.load(f)
    IDEAL = SERVER_INFO

    with patch.object(Subwinder, "_request", return_value=RESP) as mocked:
        result = Subwinder().server_info()

    assert result == IDEAL
    mocked.assert_called_once_with(Endpoints.SERVER_INFO)


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
            AuthSubwinder(*params)


@pytest.mark.skip()
def test_with():
    pass


def test__login():
    QUERIES = ("<username>", "<password>", "<useragent>")
    RESP = {"status": "200 OK", "token": "<token>"}
    CALL = (Endpoints.LOG_IN, "<username>", "<password>", "en", "<useragent>")

    _standard_asw_mock("_login", "_request", QUERIES, RESP, CALL, "<token>")


def test__logout():
    QUERIES = ()
    RESP = {"status": "200 OK", "seconds": 0.055}
    CALL = (Endpoints.LOG_OUT,)

    _standard_asw_mock("_logout", "_request", QUERIES, RESP, CALL, None)


def test_add_comment():
    QUERIES = (SEARCH_RESULT1, "bad comment", True)
    RESP = {"status": "200 OK", "seconds": "0.228"}
    CALL = (Endpoints.ADD_COMMENT, SEARCH_RESULT1.subtitles.id, "bad comment", True)

    _standard_asw_mock("add_comment", "_request", QUERIES, RESP, CALL, None)


def test_auto_update():
    PROGRAM_NAME = "SubDownloader"
    QUERIES = (PROGRAM_NAME,)
    RESP = {
        "version": "1.2.3",
        "url_windows": (
            "http://forja.rediris.es/frs/download.php/123/subdownloader1.2.3.exe"
        ),
        "url_linux": (
            "http://forja.rediris.es/frs/download.php/124/SubDownloader1.2.3.src.zip"
        ),
        "comments": "MultiUpload CDs supported(more than 2CDs)|Lots of bugs fixed",
        "status": "200 OK",
    }
    CALL = (Endpoints.AUTO_UPDATE, PROGRAM_NAME)

    _standard_asw_mock("auto_update", "_request", QUERIES, RESP, CALL, RESP)


# TODO: test this for batching
def test_download_subtitles():
    BARE_PATH = SEARCH_RESULT1.media.dirname / SEARCH_RESULT1.subtitles.filename
    BARE_QUERIES = ((SEARCH_RESULT1,),)
    BARE_CALL = (*BARE_QUERIES, [BARE_PATH])
    BARE_IDEAL = [BARE_PATH]

    FULL_PATH = Path("test dir") / "test file"
    FULL_QUERIES = ((SEARCH_RESULT1,), "test dir", "test file")
    FULL_CALL = ((SEARCH_RESULT1,), [FULL_PATH])
    FULL_IDEAL = [FULL_PATH]
    RESP = None

    asw = _dummy_auth_subwinder()

    # Test sucessfully downloading with bare params
    with patch.object(asw, "_download_subtitles", return_value=RESP) as mocked:
        # Mock out the call to get remaining downloads as 200
        with patch.object(asw, "daily_download_info", return_value=DOWNLOAD_INFO):
            result = asw.download_subtitles(*BARE_QUERIES)
    mocked.assert_called_with(*BARE_CALL)
    assert result == BARE_IDEAL

    # Test successfully downloading with full params
    with patch.object(asw, "_download_subtitles", return_value=RESP) as mocked:
        # Mock out the call to get remaining downloads as 200
        with patch.object(asw, "daily_download_info", return_value=DOWNLOAD_INFO):
            result = asw.download_subtitles(*FULL_QUERIES)
    mocked.assert_called_with(*FULL_CALL)
    assert result == FULL_IDEAL

    # Test failing from no `download_dir`
    temp_dirname = BARE_QUERIES[0][0].media.dirname
    BARE_QUERIES[0][0].media.dirname = None
    with patch.object(asw, "_download_subtitles", return_value=RESP) as mocked:
        # Mock out the call to get remaining downloads as 200
        with patch.object(asw, "daily_download_info", return_value=DOWNLOAD_INFO):
            with pytest.raises(SubDownloadError):
                result = asw.download_subtitles(*BARE_QUERIES)
    BARE_QUERIES[0][0].media.dirname = temp_dirname

    # Test failing from no `media_name` for `name_format`
    temp_filename = BARE_QUERIES[0][0].media.filename
    BARE_QUERIES[0][0].media.filename = None
    with patch.object(asw, "_download_subtitles", return_value=RESP) as mocked:
        # Mock out the call to get remaining downloads as 200
        with patch.object(asw, "daily_download_info", return_value=DOWNLOAD_INFO):
            with pytest.raises(SubDownloadError):
                result = asw.download_subtitles(
                    *BARE_QUERIES, name_format="{media_name}"
                )
    BARE_QUERIES[0][0].media.filename = temp_filename


def test__download_subtitles():
    asw = _dummy_auth_subwinder()

    RESP = {
        "status": "200 OK",
        "data": [
            {
                "idsubtitlefile": SEARCH_RESULT1.subtitles.file_id,
                "data": (
                    "H4sIAIXHxV0C/yXLwQ0CMQxE0VbmxoVCoAyzHiBS4lnFXtB2TyRuT/r6N/Yu1JuTV9"
                    "wvY9EKL8mhTmwa+2QmHRYOxiZfzuNRrVZv8dQcVk3xP08dSMFps5/4WhRKSPvwBzf2"
                    "OXZqAAAA"
                ),
            },
        ],
        "seconds": "0.397",
    }
    IDEAL_CONTENTS = (
        "Hello there, I'm that good ole compressed and encoded subtitle information"
        " that you so dearly want to save"
    )

    with TemporaryDirectory() as temp_dir:
        sub_path = Path(temp_dir) / "test download.txt"

        with patch.object(asw, "_request", return_value=RESP) as mocked:
            asw._download_subtitles([SEARCH_RESULT1], [sub_path])

        mocked.assert_called_with(
            Endpoints.DOWNLOAD_SUBTITLES, [SEARCH_RESULT1.subtitles.file_id]
        )

        # Check the contents for the correct result
        with open(sub_path) as f:
            assert f.read() == IDEAL_CONTENTS


def test_get_comments():
    # Build up the empty `SearchResult`s and add the `subtitles.id`
    queries = ([SEARCH_RESULT1, SEARCH_RESULT2],)
    with open(SAMPLES_DIR / "get_comments.json") as f:
        RESP = json.load(f)
    ideal_result = [
        [
            Comment(
                UserInfo("192696", "neo_rtr"),
                datetime(2008, 12, 14, 17, 20, 42),
                "Greate Work. thank you",
            )
        ],
        [
            Comment(
                UserInfo("745565", "pee-jay_cz"),
                datetime(2008, 12, 12, 15, 21, 48),
                "Thank you.",
            ),
            Comment(
                UserInfo("754781", "Guzeppi"),
                datetime(2008, 12, 12, 15, 51, 1),
                "You're welcome :)",
            ),
        ],
    ]
    CALL = (
        Endpoints.GET_COMMENTS,
        [SEARCH_RESULT1.subtitles.id, SEARCH_RESULT2.subtitles.id],
    )

    _standard_asw_mock("get_comments", "_request", queries, RESP, CALL, ideal_result)


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
        call(Endpoints.GUESS_MOVIE_FROM_STRING, QUERIES[:3]),
        call(Endpoints.GUESS_MOVIE_FROM_STRING, QUERIES[3:]),
    ]
    IDEAL_RESULT = [
        TvSeriesInfo("Heroes", 2006, "0813715", None, None),
        MovieInfo("Insurgent", 2015, "2908446", None, None),
        MovieInfo("Nochnoy dozor", 2004, "0403358", None, None),
        MovieInfo("Aliens", 1986, "0090605", None, None),
    ]
    with open(SAMPLES_DIR / "guess_media.json") as f:
        SAMPLE_RESP = json.load(f)

    with patch.object(asw, "_request") as mocked:
        mocked.side_effect = SAMPLE_RESP
        guesses = asw.guess_media(QUERIES)

    assert guesses == IDEAL_RESULT
    mocked.assert_has_calls(CALLS)


@pytest.mark.skip()
def test__guess_media():
    pass


def test_ping():
    RESP = {"status": "200 OK", "seconds": "0.055"}
    CALL = (Endpoints.NO_OPERATION,)

    _standard_asw_mock("ping", "_request", (), RESP, CALL, None)


def test_report_movie():
    QUERY = (SEARCH_RESULT1,)
    CALL = (Endpoints.REPORT_WRONG_MOVIE_HASH, SEARCH_RESULT1.subtitles.sub_to_movie_id)
    RESP = {"status": "200 OK", "seconds": "0.115"}

    _standard_asw_mock("report_movie", "_request", QUERY, RESP, CALL, None)


def test_search_subtitles():
    QUERIES = (((MEDIA1, "en"), (MOVIE_INFO1, "fr"), (EPISODE_INFO1, "de"),),)
    CALL = (*QUERIES, rank_search_subtitles)
    # Just testing that the correct amount of `SearchResult`s are returned
    RESP = [
        SEARCH_RESULT1,
        SEARCH_RESULT1,
        SEARCH_RESULT1,
    ]
    IDEAL = RESP

    _standard_asw_mock(
        "search_subtitles", "_search_subtitles", QUERIES, RESP, CALL, IDEAL
    )


def test__search_subtitles():
    QUERIES = (
        ((MEDIA1, "en"),),
        rank_search_subtitles,
    )
    CALL = (
        Endpoints.SEARCH_SUBTITLES,
        [
            {
                "sublanguageid": "eng",
                "moviehash": "18379ac9af039390",
                "moviebytesize": "366876694",
            },
        ],
    )
    with open(SAMPLES_DIR / "search_subtitles.json") as f:
        RESP = json.load(f)

    IDEAL = [SEARCH_RESULT2]

    _standard_asw_mock("_search_subtitles", "_request", QUERIES, RESP, CALL, IDEAL)


def test_suggest_media():
    QUERY = ("matrix",)
    CALL = (Endpoints.SUGGEST_MOVIE, "matrix")
    RESP = {
        "status": "200 OK",
        "data": {
            "matrix": [
                {
                    "MovieName": "The Matrix",
                    "MovieYear": "1999",
                    "MovieKind": "movie",
                    "IDMovieIMDB": "0133093",
                },
                {
                    "MovieName": "The Matrix Reloaded",
                    "MovieYear": "2003",
                    "MovieKind": "movie",
                    "IDMovieIMDB": "0234215",
                },
            ]
        },
    }
    IDEAL = [
        MovieInfo("The Matrix", 1999, "0133093", None, None),
        MovieInfo("The Matrix Reloaded", 2003, "0234215", None, None),
    ]

    _standard_asw_mock("suggest_media", "_request", QUERY, RESP, CALL, IDEAL)


def test_user_info():
    RESP = {
        "status": "200 OK",
        "data": {
            "IDUser": "6",
            "UserNickName": "os",
            "UserRank": "super admin",
            "UploadCnt": "296",
            "UserPreferedLanguages": "ger,eng,fre",
            "DownloadCnt": "1215",
            "UserWebLanguage": "en",
        },
        "seconds": "0.241",
    }
    CALL = (Endpoints.GET_USER_INFO,)
    IDEAL_RESULT = FULL_USER_INFO1

    _standard_asw_mock("user_info", "_request", (), RESP, CALL, IDEAL_RESULT)


def test_vote():
    INVALID_SCORES = [0, 11]
    VALID_SCORES = [1, 10]
    SAMPLE_RESP = {
        "status": "200 OK",
        "data": {
            "SubRating": "8.0",
            "SubSumVotes": "1",
            "IDSubtitle": SEARCH_RESULT1.subtitles.id,
        },
        "seconds": "0.075",
    }

    # Test valid scores
    for score in VALID_SCORES:
        query = (SEARCH_RESULT1, score)
        call = (Endpoints.SUBTITLES_VOTE, SEARCH_RESULT1.subtitles.id, score)
        _standard_asw_mock("vote", "_request", query, SAMPLE_RESP, call, None)

    # Test invalid scores
    for score in INVALID_SCORES:
        query = (SEARCH_RESULT1, score)
        call = (Endpoints.SUBTITLES_VOTE, SEARCH_RESULT1.subtitles.id, score)

        asw = _dummy_auth_subwinder()

        with patch.object(asw, "_request", return_value=SAMPLE_RESP):
            with pytest.raises(ValueError):
                print(query)
                asw.vote(*query)


def test_preview_subtitles():
    QUERIES = ([SEARCH_RESULT1, SEARCH_RESULT2],)
    CALL = ([SEARCH_RESULT1.subtitles.file_id, SEARCH_RESULT2.subtitles.file_id],)
    RESP = ["preview 1", "preview 2"]
    IDEAL = RESP

    _standard_asw_mock(
        "preview_subtitles", "_preview_subtitles", QUERIES, RESP, CALL, IDEAL
    )


def test__preview_subtitles():
    QUERIES = (["1951976245"],)
    CALL = (Endpoints.PREVIEW_SUBTITLES, QUERIES[0])
    with open(SAMPLES_DIR / "preview_subtitles.json") as f:
        RESP = json.load(f)

    IDEAL = ["1\r\n00:00:12,345 --> 00:01:23,456\r\nFirst subtitle\r\nblock"]

    _standard_asw_mock("_preview_subtitles", "_request", QUERIES, RESP, CALL, IDEAL)