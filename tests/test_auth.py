import pytest

from datetime import datetime
import json
import os
from tempfile import TemporaryDirectory
from unittest.mock import call, patch

from subwinder.auth import _build_search_query, AuthSubwinder
from subwinder.exceptions import SubAuthError
from subwinder.info import (
    Comment,
    MovieInfo,
    TvSeriesInfo,
    UserInfo,
)
from subwinder.lang import _converter
from subwinder.media import Subtitles
from subwinder.ranking import _rank_search_subtitles
from tests.constants import (
    DOWNLOAD_INFO,
    EPISODE_INFO1,
    FULL_USER_INFO1,
    MEDIA1,
    MOVIE_INFO1,
    SAMPLES_DIR,
    SEARCH_RESULT1,
    SEARCH_RESULT2,
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
    CALL = ("LogIn", "<username>", "<password>", "en", "<useragent>")

    _standard_asw_mock("_login", "_request", QUERIES, RESP, CALL, "<token>")


def test__logout():
    QUERIES = ()
    RESP = {"status": "200 OK", "seconds": 0.055}
    CALL = ("LogOut",)

    _standard_asw_mock("_logout", "_request", QUERIES, RESP, CALL, None)


def test_add_comment():
    QUERIES = (SEARCH_RESULT1, "bad comment", True)
    RESP = {"status": "200 OK", "seconds": "0.228"}
    CALL = ("AddComment", SEARCH_RESULT1.subtitles.id, "bad comment", True)

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
    CALL = ("AutoUpdate", PROGRAM_NAME)

    _standard_asw_mock("auto_update", "_request", QUERIES, RESP, CALL, RESP)


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

    _standard_asw_mock("check_subtitles", "_request", QUERIES, RESP, CALL, IDEAL_RESULT)


# TODO: test this for batching
def test_download_subtitles():
    download_path = os.path.join(
        SEARCH_RESULT1.media.dirname, SEARCH_RESULT1.subtitles.filename
    )
    QUERIES = ((SEARCH_RESULT1,),)
    RESP = None
    # Need to get the download path here
    CALL = (*QUERIES, [download_path])
    IDEAL = [download_path]

    asw = _dummy_auth_subwinder()

    with patch.object(asw, "_download_subtitles", return_value=RESP) as mocked:
        # Mock out the call to get remaining downloads as 200
        with patch.object(asw, "daily_download_info", return_value=DOWNLOAD_INFO):
            result = asw.download_subtitles(*QUERIES)

    mocked.assert_called_with(*CALL)
    assert result == IDEAL


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
        sub_path = os.path.join(temp_dir, "test download.txt")

        with patch.object(asw, "_request", return_value=RESP) as mocked:
            asw._download_subtitles([SEARCH_RESULT1], [sub_path])

        mocked.assert_called_with(
            "DownloadSubtitles", [SEARCH_RESULT1.subtitles.file_id]
        )

        # Check the contents for the correct result
        with open(sub_path) as f:
            assert f.read() == IDEAL_CONTENTS


def test_get_comments():
    # Build up the empty `SearchResult`s and add the `subtitles.id`
    queries = ([SEARCH_RESULT1, SEARCH_RESULT2],)
    with open(os.path.join(SAMPLES_DIR, "get_comments.json")) as f:
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
        "GetComments",
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


@pytest.mark.skip()
def test__guess_media():
    pass


def test_ping():
    RESP = {"status": "200 OK", "seconds": "0.055"}
    CALL = ("NoOperation",)

    _standard_asw_mock("ping", "_request", (), RESP, CALL, None)


def test_report_movie():
    QUERY = (SEARCH_RESULT1,)
    CALL = ("ReportWrongMovieHash", SEARCH_RESULT1.subtitles.sub_to_movie_id)
    RESP = {"status": "200 OK", "seconds": "0.115"}

    _standard_asw_mock("report_movie", "_request", QUERY, RESP, CALL, None)


def test_search_subtitles():
    QUERIES = (((MEDIA1, "en"), (MOVIE_INFO1, "fr"), (EPISODE_INFO1, "de"),),)
    CALL = (*QUERIES, _rank_search_subtitles)
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
        _rank_search_subtitles,
    )
    CALL = (
        "SearchSubtitles",
        [
            {
                "sublanguageid": "eng",
                "moviehash": "18379ac9af039390",
                "moviebytesize": "366876694",
            },
        ],
    )
    with open(os.path.join(SAMPLES_DIR, "search_subtitles.json")) as f:
        RESP = json.load(f)

    IDEAL = [SEARCH_RESULT2]

    _standard_asw_mock("_search_subtitles", "_request", QUERIES, RESP, CALL, IDEAL)


def test_suggest_media():
    QUERY = ("matrix",)
    CALL = ("SuggestMovie", "matrix")
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
    CALL = ("GetUserInfo",)
    IDEAL_RESULT = FULL_USER_INFO1

    _standard_asw_mock("user_info", "_request", (), RESP, CALL, IDEAL_RESULT)


def test_vote():
    SCORE = 8
    QUERIES = (SEARCH_RESULT1, SCORE)
    RESP = {
        "status": "200 OK",
        "data": {
            "SubRating": "8.0",
            "SubSumVotes": "1",
            "IDSubtitle": SEARCH_RESULT1.subtitles.id,
        },
        "seconds": "0.075",
    }
    CALL = ("SubtitlesVote", SEARCH_RESULT1.subtitles.id, SCORE)

    _standard_asw_mock("vote", "_request", QUERIES, RESP, CALL, None)


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
    CALL = ("PreviewSubtitles", QUERIES[0])
    with open(os.path.join(SAMPLES_DIR, "preview_subtitles.json")) as f:
        RESP = json.load(f)

    IDEAL = ["1\r\n00:00:12,345 --> 00:01:23,456\r\nFirst subtitle\r\nblock"]

    _standard_asw_mock("_preview_subtitles", "_request", QUERIES, RESP, CALL, IDEAL)
