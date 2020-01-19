import json
import os

from subwinder.results import SearchResult
from tests.constants import SAMPLES_DIR, SEARCH_RESULT2


def test_SearchResult():
    with open(os.path.join(SAMPLES_DIR, "search_subtitles.json")) as f:
        SAMPLE_RESP = json.load(f)["data"][0]

    sr = SearchResult.from_data(SAMPLE_RESP, None, None)
    assert sr == SEARCH_RESULT2
