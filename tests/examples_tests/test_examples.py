import filecmp
import json
import os
import shutil
import sys
from pathlib import Path
from unittest.mock import call, patch

import pytest

from dev.fake_media.fake_media import fake_media
from examples.advanced_quickstart import adv_quickstart
from examples.interactive import interative
from subwinder._constants import DEV_USERAGENT, Env
from subwinder._request import Endpoints
from tests.constants import EXAMPLES_ASSETS, EXAMPLES_RESPONSES

USERNAME = "<username>"
PASSWORD = "<password>"
USERAGENT = DEV_USERAGENT


@pytest.fixture(scope="module", autouse=True)
def set_credentials():
    # Set the fake credentials
    os.environ[Env.USERNAME.value] = USERNAME
    os.environ[Env.PASSWORD.value] = PASSWORD
    os.environ[Env.USERAGENT.value] = USERAGENT

    yield  # <-- All the tests in this module run here

    # Remove the fake credentials
    for variant in Env:
        if variant.value in os.environ:
            del os.environ[variant.value]


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
    with (EXAMPLES_RESPONSES / "interactive.json").open() as f:
        mock_request.side_effect = json.load(f)

    # Set the fake user input
    with patch("builtins.input") as mock_input:
        mock_input.side_effect = SAMPLE_INPUTS

        # Now that everything is setup let's test out the example
        LANG = "en"
        interative(LANG)

    # XXX: can do this with `filecmp`
    # Now make sure everything ended up the right way
    assert mock_request.call_args_list == CALLS
    with (tmp_path / OUT_FILE_NAME).open() as file:
        assert file.read() == SUB_FILE


# TODO: steps
# 1. Can probably strip out some of the results to slim down the file size
# 8. Expose making both dev and prog authsubwinder as a fixture
# 10. Import the base private portion, or using as to rename
# TODO: check stdout too?
@patch("subwinder._request.request")
def test_adv_quickstart(mock_request, tmp_path):
    # Setup our ideal output directory
    ideal_dir = tmp_path / "ideal"
    ideal_input = ideal_dir / "Input"
    ideal_output = ideal_dir / "Output"
    shutil.copytree(EXAMPLES_ASSETS / "adv_quickstart" / "ideal", ideal_dir)

    # Build up the dummy media since I don't want to keep it in the repo
    ENTRY_FILE = EXAMPLES_ASSETS / "adv_quickstart" / "small_entries.json"
    fake_media(ENTRY_FILE, ideal_input, entry_indicies=[5, 7, 8])
    fake_media(ENTRY_FILE, ideal_output, entry_indicies=[0, 1, 2, 3, 4, 6, 9, 10])

    # Directory for our test to use
    real_dir = tmp_path / "real"

    # Setup all the values for our example function
    AUTHOR_WHITELIST = ["breathe"]
    SUB_EXTS = ["srt"]
    LANG = "en"
    output_dir = real_dir / "Output"
    LEDGER = real_dir / "ledger.json"

    # Setup fake media in our test input directory
    input_dir = real_dir / "Input"
    fake_media(ENTRY_FILE, input_dir, entry_indicies=range(11))

    # Calls to verify against
    search_values = [
        ("dd68b108d270aa7b", "732924"),
        ("6e02ec9fdf3c200f", "1251826"),
        ("579bfcd8ee87dff3", "1529505"),
        ("7d87bae932a2e533", "2632612"),
        ("c47cb30ab992fb34", "730435"),
        ("18379ac9af039390", "366876"),
        ("e1966a88db8f4a48", "948792"),
        ("4f47a0266f3d15c5", "1743776"),
        ("09a2c497663259cb", "733589"),
        ("b5a6939c71a6c3b6", "758756"),
        ("2ef61c586962b462", "1322969"),
    ]
    search_calls = []
    for hash, size in search_values:
        query = [{"sublanguageid": "eng", "moviehash": hash, "moviebytesize": size}]
        search_calls.append(call(Endpoints.SEARCH_SUBTITLES, "<token>", query))

    CALLS = [
        call(Endpoints.LOG_IN, None, USERNAME, PASSWORD, "en", USERAGENT),
        *search_calls,
        call(Endpoints.SERVER_INFO, "<token>"),
        call(Endpoints.SERVER_INFO, "<token>"),
        call(
            Endpoints.DOWNLOAD_SUBTITLES,
            "<token>",
            [
                "1955750684",
                "1953621390",
                "1952941557",
                "1953552171",
                "1952200785",
                "235409",
                "1952149026",
                "1954434245",
            ],
        ),
        call(Endpoints.LOG_OUT, "<token>"),
    ]

    # Set the fake responses
    with (EXAMPLES_RESPONSES / "adv_quickstart.json").open() as f:
        mock_request.side_effect = json.load(f)

    # Need to mock out glob here since the return order isn't guaranteed and I need it
    # to be consitent for testing. Because glob is a generator and I won't know the
    # files returned till runtime (for flexibility) the best method I've settled on is
    # to run the same glob beforehand and then use the results for the mocked generator.
    # This could be avoided if I could still somehow access the original `glob` method
    # from within the patched generator, but I couldn't find a way to do that.
    items = list(input_dir.glob("**/*"))

    def _sorted_glob(self, glob):
        # Sort values ignoring case (case causes issues since some filesystems are case
        # sensitive while others aren't)
        items.sort(key=lambda val: str(val).lower())
        for item in items:
            yield item

    with patch.object(Path, "glob", new=_sorted_glob):
        # Run the example
        adv_quickstart(input_dir, output_dir, LEDGER, LANG, AUTHOR_WHITELIST, SUB_EXTS)

    # Verify the calls to `request` look good
    assert mock_request.call_args_list == CALLS

    def sorted_rel_files(directory):
        files = []
        dir_str = str(directory) + os.sep

        for item in directory.glob("**/*"):
            if item.is_file():
                item = str(item)
                files.append(item.replace(dir_str, ""))

        files.sort()
        return files

    # Verify the ideal and test directory is the same
    # they being ignored by default?
    real_files = sorted_rel_files(real_dir)
    ideal_files = sorted_rel_files(ideal_dir)

    assert ideal_files == real_files
    match, mismatch, errors = filecmp.cmpfiles(real_dir, ideal_dir, real_files)
    print(f"Mismatch: {mismatch}", file=sys.stderr)
    print(f"Errors: {errors}", file=sys.stderr)
    assert len(mismatch) == 0
    assert len(errors) == 0
