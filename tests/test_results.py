import pytest

from datetime import datetime
import json
import os

from subwinder.info import EpisodeInfo, SubtitlesInfo, UserInfo
from subwinder.results import SearchResult
from tests.constants import SAMPLES_DIR


def test_SearchResult():
    with open(os.path.join(SAMPLES_DIR, "search_subtitles.json")) as f:
        SAMPLE_RESP = json.load(f)["data"][0]

    # TODO: implement from_data for here
    sr = SearchResult.from_data(SAMPLE_RESP, "dir", "file")
    assert sr.author == UserInfo("1332962", "elderman")
    assert sr.media == EpisodeInfo(
        '"Fringe" Alone in the World', 2011, "1998676", 4, 3, "dir", "file"
    )
    # TODO: add from_data here
    assert sr.subtitles == SubtitlesInfo(
        58024,
        57765,
        0,
        0.0,
        "4251071",
        "1952941557",
        "Fringe.S04E03.HDTV.XviD-LOL.srt",
        "en",
        "eng",
        "srt",
        "UTF-8",
    )
    assert sr.upload_date == datetime(2011, 10, 8, 7, 36, 1)
