from datetime import timedelta
from unittest.mock import call, patch

from subwinder.base import SubWinder
from subwinder.lang import (
    _LangConverter,
    LangFormat,
    _converter,
    lang_2s,
    lang_3s,
    lang_longs,
)

RESP = [
    {"ISO639": "de", "SubLanguageID": "ger", "LanguageName": "German"},
    {"ISO639": "en", "SubLanguageID": "eng", "LanguageName": "English"},
    {"ISO639": "fr", "SubLanguageID": "fre", "LanguageName": "French"},
]


def test_LangConverter():
    converter = _LangConverter()
    assert converter._last_updated is None

    with patch.object(
        SubWinder, "_get_languages", return_value=RESP
    ) as mocked:
        # After first update converter shouldn't request again for an hour
        converter._update()

        # These will not call `_get_languages`
        converter._update()
        assert "eng" == converter.convert(
            "en", LangFormat.LANG_2, LangFormat.LANG_3
        )
        assert "English" == converter.convert(
            "eng", LangFormat.LANG_3, LangFormat.LANG_LONG
        )
        assert ["de", "en", "fr"] == converter.list(LangFormat.LANG_2)
        assert ["ger", "eng", "fre"] == converter.list(LangFormat.LANG_3)
        assert ["German", "English", "French"] == converter.list(
            LangFormat.LANG_LONG
        )

        # `_get_languages` should only be called once
        mocked.assert_called_once_with()

        # Now wait long enough that we will refresh the langs
        converter._last_updated -= timedelta(seconds=3600)
        converter.list(LangFormat.LANG_2)
        mocked.assert_has_calls([call(), call()])


def test_globals():
    # Reset converter if needed
    _converter._last_updated = None

    with patch.object(
        SubWinder, "_get_languages", return_value=RESP
    ) as mocked:
        # Check all the conversions
        assert "eng" == lang_2s.convert("en", LangFormat.LANG_3)
        assert "English" == lang_3s.convert("eng", LangFormat.LANG_LONG)
        assert "en" == lang_longs.convert("English", LangFormat.LANG_2)

        # Check all the listings
        assert ["de", "en", "fr"] == lang_2s.list()
        assert ["ger", "eng", "fre"] == lang_3s.list()
        assert ["German", "English", "French"] == lang_longs.list()

        # `_get_languages` should only be called once
        mocked.assert_called_once_with()
