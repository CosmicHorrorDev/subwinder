import filecmp
import json
import os
import sys
from pathlib import Path
from unittest.mock import call, patch

import pytest

from dev.fake_media.fake_media import fake_media
from examples.advanced_quickstart import adv_quickstart
from examples.interactive import interative
from subwinder._constants import DEV_USERAGENT, Env
from subwinder._request import Endpoints
from subwinder.media import Media
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
        RESPS = json.load(f)
    mock_request.side_effect = RESPS

    with patch("builtins.input") as mock_input:
        # Set the fake user input
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
# 6. Add test extract and pack with one sample, and with randomly generated input
# 7. Add test for faking media
#    - Test that it's sparse
#    - Test on single value
#    - Test on some random data as well (limit size to something like 1MB?)
# 8. Expose making both dev and prog authsubwinder as a fixture
# 10. Import the base private portion, or using as to rename
# TODO: check stdout too?
@pytest.mark.io_heavy(
    "Playing it safe due to large files if sparse files fail. An unmarked test using"
    " smaller sparse files should pick this up instead"
)
@patch("subwinder._request.request")
def test_adv_quickstart(mock_request, tmp_path):
    # Setup all the values for our test
    AUTHOR_WHITELIST = ["breathe"]
    SUB_EXTS = ["srt"]
    LANG = "en"
    output_dir = tmp_path / "Output"
    LEDGER = tmp_path / "ledger.json"

    # Setup fake media in our input directory
    input_dir = tmp_path / "Input"
    input_dir.mkdir()
    fake_media(output_dir=input_dir, entry_indicies=range(11))

    # Calls to verify against
    search_values = [
        ("dd68b108d270aa7b", "732924242"),
        ("6e02ec9fdf3c200f", "1251826386"),
        ("579bfcd8ee87dff3", "1529505156"),
        ("7d87bae932a2e533", "2632612813"),
        ("c47cb30ab992fb34", "730435584"),
        ("18379ac9af039390", "366876694"),
        ("e1966a88db8f4a48", "948792230"),
        ("4f47a0266f3d15c5", "1743776999"),
        ("09a2c497663259cb", "733589504"),
        ("b5a6939c71a6c3b6", "758756235"),
        ("2ef61c586962b462", "1322969681"),
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
        RESPS = json.load(f)
    mock_request.side_effect = RESPS

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

    # Verify all the new files look right
    adv_quickstart_assets = EXAMPLES_ASSETS / "adv_quickstart"
    sub_files = [
        Path("Output") / "Carnival of Souls (1962).eng.srt",
        Path("Output") / "Detour (1945).eng.srt",
        Path("Output") / "Fringe - s04e03 - Alone in the World.eng.srt",
        Path("Output") / "McLintock (1963).eng.srt",
        Path("Output") / "Night of the Living Dead (1968).eng.srt",
        Path("Output") / "Night Watch (2004).eng.srt",
        Path("Output") / "Plan 9 from Outer Space (1959).eng.srt",
        Path("Output") / "The Last Man on Earth (1964).eng.srt",
    ]
    ledger_file = "ledger.json"

    match, mismatch, errors = filecmp.cmpfiles(
        tmp_path, adv_quickstart_assets, [*sub_files, ledger_file]
    )
    print(f"Mismatched: {mismatch}", file=sys.stderr)
    print(f"Errors: {errors}", file=sys.stderr)
    assert len(mismatch) == 0
    assert len(errors) == 0

    # And lastly verify that all the media still seems good (Would be easier if this was
    # included in the repo, but I don't trust everything to treat it as sparse files)
    # TODO: building up identical media in the temp dir is also an option and allows us
    # to just compare the two different directories which could easily be worth it
    no_match_params = [
        ("dd68b108d270aa7b", 732924242, input_dir, "Algiers (1938).dummy"),
        ("579bfcd8ee87dff3", 1529505156, input_dir, "Charade (1963).dummy"),
        ("7d87bae932a2e533", 2632612813, input_dir, "Cyrano de Bergerac (1950).dummy"),
    ]
    match_params = [
        ("6e02ec9fdf3c200f", 1251826386, output_dir, "Carnival of Souls (1962).dummy"),
        ("c47cb30ab992fb34", 730435584, output_dir, "Detour (1945).dummy"),
        (
            "18379ac9af039390",
            366876694,
            output_dir,
            "Fringe - s04e03 - Alone in the World.dummy",
        ),
        ("e1966a88db8f4a48", 948792230, output_dir, "McLintock (1963).dummy"),
        (
            "4f47a0266f3d15c5",
            1743776999,
            output_dir,
            "Night of the Living Dead (1968).dummy",
        ),
        ("09a2c497663259cb", 733589504, output_dir, "Night Watch (2004).dummy"),
        (
            "b5a6939c71a6c3b6",
            758756235,
            output_dir,
            "Plan 9 from Outer Space (1959).dummy",
        ),
        (
            "2ef61c586962b462",
            1322969681,
            output_dir,
            "The Last Man on Earth (1964).dummy",
        ),
    ]
    no_match = [Media.from_parts(*params) for params in no_match_params]
    match = [Media.from_parts(*params) for params in match_params]

    for file in input_dir.glob("*.dummy"):
        media = Media(file)
        assert media in no_match
        no_match.remove(media)

    for file in output_dir.glob("*.dummy"):
        media = Media(file)
        assert media in match
        match.remove(media)

    assert len(no_match) == 0
    assert len(match) == 0
