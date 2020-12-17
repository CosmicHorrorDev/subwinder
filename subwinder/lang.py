# Note: this whole file uses enough global variables to make my skin crawl, but I can't
# really think of a nicer way of exposing everything
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# See: https://github.com/LovecraftianHorror/subwinder/issues/52#issuecomment-637333960
# if you want to know why `request` isn't imported with `from`
import subwinder._request
from subwinder._request import Endpoints
from subwinder.exceptions import SubLangError


class _LangKey(Enum):
    LANG_2 = "ISO639"
    LANG_3 = "SubLanguageID"
    LANG_LONG = "LanguageName"

    @classmethod
    def from_format(cls, lang_format):
        KEYS = [cls.LANG_2, cls.LANG_3, cls.LANG_LONG]
        return KEYS[lang_format.value]


class LangFormat(Enum):
    LANG_2 = 0
    LANG_3 = 1
    LANG_LONG = 2


class _LangConverter:
    """
    This class is used as a common converter to cache the language response from the API
    and handle converting between the separate forms. Caching in this way limits
    unnecessary requests to the API along with setting up an easy way to convert between
    any of the forms.
    """

    def __init__(self):
        self.default()

    def _fetch(self):
        return subwinder._request.request(Endpoints.GET_SUB_LANGUAGES, None)["data"]

    def _maybe_update(self, force=False):
        # Language list should refresh every hour, return early if still fresh unless
        # update is `force`d
        if not force and self._last_updated is not None:
            if (datetime.now() - self._last_updated).total_seconds() < 3600:
                return

        # Get language list from api
        lang_sets = self._fetch()

        # Reset then recollect info
        self.default()
        for lang_set in lang_sets:
            for lang_format in LangFormat:
                lang = lang_set[_LangKey.from_format(lang_format).value]
                self._langs[lang_format.value].append(lang)

        # Refresh updated time
        self._last_updated = datetime.now()

    def default(self):
        self.set(None, [[] for _ in list(LangFormat)])

    def dump(self):
        last_updated = self._last_updated
        langs = self._langs

        self.default()

        return last_updated, langs

    def set(self, last_updated, langs):
        self._last_updated = last_updated
        self._langs = langs

    def convert(self, lang, from_format, to_format):
        self._maybe_update()

        try:
            lang_index = self._langs[from_format.value].index(lang)
        except ValueError:
            raise SubLangError(
                f"Tried to convert language '{lang}', but not found in language list:"
                f" {self._langs[from_format.value]}"
            )

        return self._langs[to_format.value][lang_index]

    def list(self, lang_format):
        self._maybe_update()

        return self._langs[lang_format.value]


# `_converter` shared by all the `_Lang`s
_converter = _LangConverter()


@dataclass
class _Lang:
    """
    Class that represents all actions for one of the three lang formats returned by the
    API. each `_Lang` shares a common `_converter` to try and reduce API calls as much
    as possible. You should be using the global `lang_2s`, `lang_3s`, and `lang_longs`
    instead of building more of these (hence it being private).
    """

    _format: LangFormat

    def __iter__(self):
        return iter(_converter.list(self._format))

    def __len__(self):
        return len(_converter.list(self._format))

    # TODO: Rename to `convert_to` to make it obvious?
    def convert(self, lang, to_format):
        """
        Convert the `lang` from the current format to `to_format`.
        """
        return _converter.convert(lang, self._format, to_format)


lang_2s = _Lang(LangFormat.LANG_2)
lang_3s = _Lang(LangFormat.LANG_3)
lang_longs = _Lang(LangFormat.LANG_LONG)
