import pytest

from datetime import datetime
import json
import os
from unittest.mock import patch

from subwinder.base import Subwinder
from subwinder.lang import _converter
from tests.constants import DOWNLOAD_INFO, SAMPLES_DIR, SERVER_INFO


LANGS = [
    ("de", "ger", "German"),
    ("en", "eng", "English"),
    ("fr", "fre", "French"),
]
# Fake already updated langs
_converter._langs = LANGS
_converter._last_updated = datetime.now()


@pytest.mark.skip(reason="Only passes the values onto `_request`")
def test__request():
    pass


def test_daily_download_info():
    with open(os.path.join(SAMPLES_DIR, "server_info.json")) as f:
        RESP = json.load(f)
    IDEAL = DOWNLOAD_INFO

    with patch.object(Subwinder, "_request", return_value=RESP) as mocked:
        result = Subwinder().daily_download_info()

    assert result == IDEAL
    mocked.assert_called_once_with("ServerInfo")


def test_get_languages():
    sw = Subwinder()
    assert sw.get_languages() == LANGS


def test_server_info():
    with open(os.path.join(SAMPLES_DIR, "server_info.json")) as f:
        RESP = json.load(f)
    IDEAL = SERVER_INFO

    with patch.object(Subwinder, "_request", return_value=RESP) as mocked:
        result = Subwinder().server_info()

    assert result == IDEAL
    mocked.assert_called_once_with("ServerInfo")
