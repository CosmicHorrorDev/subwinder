import pytest

from datetime import datetime

from subwinder.base import Subwinder
from subwinder.lang import _converter


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


def test_get_languages():
    sw = Subwinder()
    assert sw.get_languages() == LANGS


@pytest.mark.skip(
    reason="Currently just calls the API, and method is likely to change"
)
def test_server_info():
    pass
