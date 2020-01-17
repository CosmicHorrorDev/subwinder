import pytest

from datetime import datetime
import json
import os
from tempfile import TemporaryDirectory
from unittest.mock import call, patch

from subwinder.auth import _build_search_query, AuthSubwinder
from subwinder.exceptions import SubAuthError
from subwinder.info import (
    build_media_info,
    Comment,
    EpisodeInfo,
    FullUserInfo,
    MovieInfo,
    SubtitlesInfo,
    TvSeriesInfo,
    UserInfo,
)
from subwinder.lang import _converter
from subwinder.media import Media, Subtitles
from subwinder.ranking import _rank_search_subtitles
from subwinder.results import SearchResult
from tests.constants import SAMPLES_DIR


# Fake already updated langs to prevent API requests
_converter._langs = [
    ("de", "ger", "German"),
    ("en", "eng", "English"),
    ("fr", "fre", "French"),
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
            (Media("0123456789abcdef", 123456), "en"),
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
            (EpisodeInfo(None, None, "EI imdbid", None, None, 1, 2), "de"),
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


@pytest.mark.skip(reason="Method not implemented yet")
def test_add_comment():
    pass


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


# TODO: test this for batching
def test_download_subtitles():
    download_path = os.path.join("movie dir", "sub filename.sub ext")
    queries = ((SearchResult.__new__(SearchResult),),)
    queries[0][0].media = MovieInfo("Insurgent", 2015, "2908446", None, None)
    queries[0][0].media.dirname = "movie dir"
    queries[0][0].media.filename = "movie filename"
    queries[0][0].subtitles = SubtitlesInfo.__new__(SubtitlesInfo)
    queries[0][0].subtitles.filename = "sub filename.sub ext"
    queries[0][0].subtitles.lang_2 = "sub lang 2"
    queries[0][0].subtitles.lang_3 = "sub lang 3"
    queries[0][0].subtitles.ext = "sub ext"
    RESP = None
    # Need to get the download path here
    CALL = (*queries, [download_path])
    IDEAL = ["movie dir/sub filename.sub ext"]

    _standard_asw_mock(
        "download_subtitles", "_download_subtitles", queries, RESP, CALL, IDEAL
    )


def test__download_subtitles():
    asw = _dummy_auth_subwinder()

    dummy_search_result = SearchResult.__new__(SearchResult)
    dummy_search_result.subtitles = SubtitlesInfo.__new__(SubtitlesInfo)
    dummy_search_result.subtitles.encoding = "UTF-8"
    dummy_search_result.subtitles.file_id = "1954677189"
    RESP = {
        "status": "200 OK",
        "data": [
            {
                "idsubtitlefile": "1954677189",
                "data": (
                    "H4sIAIXHxV0C/yXLwQ0CMQxE0VbmxoVCoAyzHiBS4lnFXtB2TyRuT/r6N"
                    "/Yu1JuTV9wvY9EKL8mhTmwa+2QmHRYOxiZfzuNRrVZv8dQcVk3xP08dSM"
                    "Fps5/4WhRKSPvwBzf2OXZqAAAA"
                ),
            },
        ],
        "seconds": "0.397",
    }
    IDEAL_CONTENTS = (
        "Hello there, I'm that good ole compressed and encoded subtitle"
        " information that you so dearly want to save"
    )

    with TemporaryDirectory() as temp_dir:
        sub_path = os.path.join(temp_dir, "test download.txt")

        with patch.object(asw, "_request", return_value=RESP) as mocked:
            asw._download_subtitles([dummy_search_result], [sub_path])

        mocked.assert_called_with("DownloadSubtitles", ["1954677189"])

        # Check the contents for the correct result
        with open(sub_path) as f:
            assert f.read() == IDEAL_CONTENTS


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
    CALL = ("GetComments", ["3387112", "3385570"])

    _standard_asw_mock(
        "get_comments", "_request", queries, RESP, CALL, ideal_result
    )


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
    query = (SearchResult.__new__(SearchResult),)
    query[0].subtitles = SubtitlesInfo.__new__(SubtitlesInfo)
    query[0].subtitles.sub_to_movie_id = "739"
    CALL = ("ReportWrongMovieHash", "739")
    RESP = {"status": "200 OK", "seconds": "0.115"}

    _standard_asw_mock("report_movie", "_request", query, RESP, CALL, None)


def test_search_subtitles():
    QUERIES = (
        (
            (Media.__new__(Media), "en"),
            (MovieInfo.__new__(MovieInfo), "fr"),
            (EpisodeInfo.__new__(EpisodeInfo), "de"),
        ),
    )
    CALL = (*QUERIES, _rank_search_subtitles)
    RESP = [
        SearchResult.__new__(SearchResult),
        SearchResult.__new__(SearchResult),
        SearchResult.__new__(SearchResult),
    ]
    IDEAL = RESP

    _standard_asw_mock(
        "search_subtitles", "_search_subtitles", QUERIES, RESP, CALL, IDEAL
    )


def test__search_subtitles():
    queries = (
        ((Media("18379ac9af039390", 366876694), "en"),),
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

    sr = SearchResult(
        UserInfo("1332962", "elderman"),
        EpisodeInfo(
            '"Fringe" Alone in the World', 2011, "1998676", None, None, 4, 3
        ),
        SubtitlesInfo.__new__(SubtitlesInfo),
        datetime(2011, 10, 8, 7, 36, 1),
    )
    print(build_media_info(RESP["data"][0]))
    ideal = [sr]
    ideal[0].subtitles.size = 58024
    ideal[0].subtitles.downloads = 57765
    ideal[0].subtitles.num_comments = 0
    ideal[0].subtitles.rating = None
    ideal[0].subtitles.id = "4251071"
    ideal[0].subtitles.file_id = "1952941557"
    ideal[0].subtitles.sub_to_movie_id = "3585468"
    ideal[0].subtitles.filename = "Fringe.S04E03.HDTV.XviD-LOL.srt"
    ideal[0].subtitles.lang_2 = "en"
    ideal[0].subtitles.lang_3 = "eng"
    ideal[0].subtitles.ext = "srt"
    ideal[0].subtitles.encoding = "UTF-8"

    _standard_asw_mock(
        "_search_subtitles", "_request", queries, RESP, CALL, ideal
    )


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
    # TODO: switching this out to `from_data` would make it simpler
    ideal_result = FullUserInfo.__new__(FullUserInfo)
    ideal_result.id = "6"
    ideal_result.nickname = "os"
    ideal_result.rank = "super admin"
    ideal_result.uploads = 296
    ideal_result.downloads = 1215
    ideal_result.preferred_languages = ["de", "en", "fr"]
    ideal_result.web_language = "en"

    _standard_asw_mock("user_info", "_request", (), RESP, CALL, ideal_result)
