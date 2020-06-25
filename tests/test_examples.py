import pytest

from dev.fake_media import fake_media
from examples.advanced_quickstart import adv_quickstart
from examples.interactive import interative
from subwinder._request import Endpoints
from tests.constants import REPO_DIR, SAMPLES_DIR
from tests.conftest import skip_non_default

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


@pytest.fixture(scope="module")
def gen_fake_media(request):
    # Generating media is expensive so only run if we're running io_heavy tests
    if skip_non_default(request):
        # Empty yield to keep pytest happy. No tests should use this in this case
        yield  # <-- NO TESTS!
    else:
        entries_file = REPO_DIR / "dev" / "fake_media_entries.json"

        with TemporaryDirectory() as temp_dir:
            fake_media_paths = fake_media(entries_file, Path(temp_dir))
            assert fake_media_paths, "Tests should have at least one dummy file"
            yield fake_media_paths  # <-- Run all tests


# TODO: verify stdout looks good too
@patch("subwinder._request.request")
def test_interactive(mock_request, tmp_path):
    SAMPLE_INPUTS = [
        "mr robot",  # Media to search for
        "0",  # Select Mr. Robot TV Series
        "1",  # Season for tv series
        "2",  # Episode for tv series
        "1",  # Select 2nd subtitles
        "y",  # Yes to download after preview
        tmp_path,  # Download them to the temp dir
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
            [{"sublanguageid": "eng", "imdbid": "4158110", "season": 1, "episode": 2}],
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

    with patch("builtins.input") as mock_input:
        # Set the fake user input
        mock_input.side_effect = SAMPLE_INPUTS

        # Now that everything is setup let's test out the example
        LANG = "en"
        interative(LANG)

        # Now make sure everything ended up the right way
        mock_request.assert_has_calls(CALLS)
        with (tmp_path / OUT_FILE_NAME).open() as file:
            assert file.read() == SUB_FILE


# FIXME: likely don't use `tmp_path` here, it doesn't automatically get cleaned up
@pytest.mark.io_heavy
def test_adv_quickstart(gen_fake_media, tmp_path):
    fake_media_paths = gen_fake_media

    # Setup all the values for our test
    # TODO: fix these (make sure they test stuff)
    AUTHOR_WHITELIST = []
    SUB_EXTS = []
    LANG = "en"
    input_dir = fake_media_paths[0].parent
    output_dir = tmp_path
    saved_subs_file = output_dir / "ledger.json"
    # TODO: still need to get the values from the actual requests here
    # TODO: ensure everything runs right
    # TODO: move all the files back to their right place
    # TODO: ensure ledger has the right info
