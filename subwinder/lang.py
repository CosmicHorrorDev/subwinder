# Note: this whole file uses enough global variables to make my skin crawl,
#       but I can't really think of a nicer way of exposing everything
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from subwinder.exceptions import SubLangError
from subwinder.request import _request


_LANG_2_KEY = "ISO639"
_LANG_3_KEY = "SubLanguageID"
_LANG_LONG_KEY = "LanguageName"


class LangFormat(Enum):
    LANG_2 = 0
    LANG_3 = 1
    LANG_LONG = 2


class _LangConverter:
    """
    This class is used as a common converter to cache the language response
    from the API and handle converting between the separate forms. Caching in
    this way limits unnecessary requests to the API along with setting up an
    easy way to convert between any of the forms.
    """
    def __init__(self):
        self._last_updated = None

    def _fetch(self):
        return _request("GetSubLanguages", None)["data"]

    def _update(self, force=False):
        # Language list should refresh every hour, return early if still fresh
        # unless update is `force`d
        if not force and self._last_updated is not None:
            if (datetime.now() - self._last_updated).total_seconds() < 3600:
                return

        # Get language list from api
        lang_sets = self._fetch()

        # Store `langs` in common format
        self._langs = []
        for lang_set in lang_sets:
            lang_2 = lang_set[_LANG_2_KEY]
            lang_3 = lang_set[_LANG_3_KEY]
            lang_name = lang_set[_LANG_LONG_KEY]

            self._langs.append((lang_2, lang_3, lang_name))

        # Refresh updated time
        self._last_updated = datetime.now()

    def convert(self, lang, from_format, to_format):
        # This isn't the most efficient way to convert formats, but there's
        # less than 100 languages supported so it really  shouldn't be a
        # bottleneck. If it's a problem it can be optimized

        # Update `langs` listing if needed
        self._update()

        # Hopefully no one tries to convert this way, but included just in case
        if from_format == to_format:
            return lang

        for lang_set in self._langs:
            # Return converted language on match
            if lang == lang_set[from_format.value]:
                return lang_set[to_format.value]

        # If we got here then the `lang` isn't in the listing, raise error
        raise SubLangError(
            f"Tried to convert language '{lang}', but not found in language"
            f" list {self._langs}"
        )

    def list(self, lang_format):
        # Update if needed
        self._update()

        return [lang_set[lang_format.value] for lang_set in self._langs]


# `_converter` shared by all the `_Lang`s
_converter = _LangConverter()


@dataclass
class _Lang:
    _format: LangFormat

    def __contains__(self, lang):
        return lang in _converter.list(self._format)

    def __getitem__(self, i):
        return list(self)[i]

    def __iter__(self):
        return iter(_converter.list(self._format))

    def __len__(self):
        return len(_converter.list(self._format))

    def convert(self, lang, to_format):
        return _converter.convert(lang, self._format, to_format)


lang_2s = _Lang(LangFormat.LANG_2)
lang_3s = _Lang(LangFormat.LANG_3)
lang_longs = _Lang(LangFormat.LANG_LONG)
