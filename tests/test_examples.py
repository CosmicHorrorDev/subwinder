import pytest

from examples.interactive import interative
from subwinder._request import Endpoints
from tests.constants import SAMPLES_DIR

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import call, patch


USERNAME = "<username>"
PASSWORD = "<password>"
USERAGENT = "<useragent>"


@pytest.fixture(scope="module", autouse=True)
def set_credentials():
    # Set the fake credentials
    os.environ["OPEN_SUBTITLES_USERNAME"] = USERNAME
    os.environ["OPEN_SUBTITLES_PASSWORD"] = PASSWORD
    os.environ["OPEN_SUBTITLES_USERAGENT"] = USERAGENT

    yield  # <-- All the tests in this module run here

    # Remove the fake credentials
    del os.environ["OPEN_SUBTITLES_USERNAME"]
    del os.environ["OPEN_SUBTITLES_PASSWORD"]
    del os.environ["OPEN_SUBTITLES_USERAGENT"]


@patch("subwinder._request.request")
def test_interactive(mock_request):
    with TemporaryDirectory() as temp_dir:
        SAMPLE_INPUTS = [
            "mr robot",  # Media to search for
            "0",  # Select Mr. Robot TV Series
            "1",  # Season for tv series
            "2",  # Episode for tv series
            "1",  # Select 2nd subtitles
            "y",  # Yes to download after preview
            temp_dir,  # Download them to the temp dir
        ]
        TOKEN = "<token>"
        SUB_ID = "1954809953"
        OUT_FILE_NAME = "Mr.Robot.S01E02.HDTV.x264-KILLERS.srt"
        SUB_FILE = "1\n00:00:12,345 --> 00:01:23,456\nFirst subtitle\nblock"
        CALLS = [
            call(Endpoints.LOG_IN, None, USERNAME, PASSWORD, "en", USERAGENT),
            call(Endpoints.GET_USER_INFO, TOKEN),
            call(Endpoints.SERVER_INFO, TOKEN),
            call(Endpoints.SUGGEST_MOVIE, TOKEN, SAMPLE_INPUTS[0]),
            call(
                Endpoints.SEARCH_SUBTITLES,
                TOKEN,
                [
                    {
                        "sublanguageid": "eng",
                        "imdbid": "4158110",
                        "season": 1,
                        "episode": 2,
                    }
                ],
            ),
            call(Endpoints.PREVIEW_SUBTITLES, TOKEN, [SUB_ID]),
            call(Endpoints.SERVER_INFO, TOKEN),
            call(Endpoints.DOWNLOAD_SUBTITLES, TOKEN, [SUB_ID]),
            call(Endpoints.LOG_OUT, TOKEN),
        ]

        # Set the fake responses
        with (SAMPLES_DIR / "example_interactive.json").open() as f:
            RESPS = json.load(f)
        mock_request.side_effect = RESPS

        with patch("builtins.input") as mock:
            # Set the fake user input
            mock.side_effect = SAMPLE_INPUTS

            # Now that everything is setup lets test out the example
            LANG = "en"
            interative(LANG)

            # Now make sure everything ended up the right way
            mock_request.assert_has_calls(CALLS)
            with (Path(temp_dir) / OUT_FILE_NAME).open() as file:
                assert file.read() == SUB_FILE
