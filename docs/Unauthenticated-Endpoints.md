# Unauthenticated Endpoints

All functionality with the unauthenticated API are exposed directly from the [`Subwinder Object`](#subwinder) and the [`subwinder.lang`](#subwinderlang-module) module.

---

## Table of Contents

* [`Subwinder`](#subwinder)
    * [Initialization](#initialization)
    * [`.daily_download_info()`](#daily_download_info)
    * [`.get_languages()`](#get_languages)
    * [`.server_info()`](#server_info)
* [`subwinder.lang` module](#subwinderlang-module)
    * [`lang_2s`, `lang_3s`, and `lang_longs`](#lang_2s-lang_3s-and-lang_longs)
        * [`.convert()`](#convertlang-to_format)
        * [`<lang> in lang_2s`](#lang-in-lang_2s-__contains__lang)
        * [`lang_3s[<index>]`](#lang_3sindex-__getitem__index)
        * [`iter(lang_longs)`](#iterlang_longs-__iter__)
        * [`len(lang_2s)`](#lenlang_2s-__len__)

---

### `Subwinder`

This class provides the functionality of the unauthenticated API.

```python
from subwinder import Subwinder
```

#### Initialization

 `Subwinder`'s constructor takes no values.

```python
sw = Subwinder()
```

#### `.daily_download_info()`

Gets information covering the user's daily download information in the form of a [`DownloadInfo`](Custom-Classes.md#downloadinfo) object. This information is also exposed through the `.server_info()` method.

**Returns:** A [`DownloadInfo`](Custom-Classes.md#downloadinfo) object covering daily download information for the current user.

```python
from subwinder.info import DownloadInfo


sw = Subwinder()
assert type(sw.daily_download_info()) == DownloadInfo
```

#### `.get_languages()`

Languages for opensubtitles.org seem to follow the [ISO 639-1 and ISO 639-2/B](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) language specifications.

**Returns:** A list of the supported language codes in tuples consisting of the 2 letter, 3 letter, and long form for each supported language.

```python
sw = Subwinder()
assert sw.get_languages() == [
    ("ab", "abk", "Abkhazian"),
    ("af", "afr", "Afrikaans"),
    ...
    ("vi", "vie", "Vietnamese"),
]
```

#### `.server_info()`

Lists various information about the opensubtitles server in the form of a [`ServerInfo`](Custom-Classes.md#serverinfo) object.

**Returns:** A [`ServerInfo`](Custom-Classes.md#serverinfo) object listing various information on the opensubtitles server.

```python
from subwinder.info import ServerInfo


sw = Subwinder()
assert type(sw.server_info()) == ServerInfo
```

---

## `subwinder.lang` module

This module contains the `Enum` `LangFormat` and the global `_Lang` objects [`lang_2s`, `lang_3s`, and `lang_longs`](#lang_2s-lang_3s-and-lang_longs). The `LangFormat` just contains information for converting between the different formats while each of the global objects have the following functionality.

```python
from subwinder.lang import LangFormat, lang_2s, lang_3s, lang_longs
# This is considered private, only used here for demonstration purposes
from subwinder.lang import _Lang

assert type(lang_2s) == _Lang
```

### `lang_2s`, `lang_3s`, and `lang_longs`

The global objects used to perform the language conversion and listing operations of the API. Used to cache the language response from the API, cache is automatically updated hourly to ensure things like daemons will still have updated language lists. These objects are already created so there is no initialization needed.

#### `.convert(lang, to_format)`

Converts the provided `lang` from the global object's format to the provided `to_format`.

| Param | Type | Description |
| :---: | :---: | :--- |
| `lang` | `str` | The language tag you would like to convert |
| `to_format` | `LangFormat` value | The format `lang` is converted to |

**Returns:** `lang` in the format of `to_format`.

```python
assert lang_2s.convert("en", LangFormat.LANG_3) == "eng"
assert lang_3s.convert("eng", LangFormat.LANG_LONG) == "English"
assert lang_longs.convert("English", LangFormat.LANG_2) == "en"
```

#### `<lang> in lang_2s` (`.__contains__(<lang>)`)

Checks if `<lang>` is in the listings contained by `lang_2s`, `lang_3s`, or `lang_longs`.

```python
assert "en" in lang_2s
assert "eng" in lang_3s
assert "English" in lang_longs
```

#### `lang_3s[<index>]` (`.__getitem__(<index>)`)

Returns the value stored at `<index>` location in either `lang_2s`, `lang_3`, or `lang_longs`.

```python
assert lang_2s[0] == "ab"
assert lang_3s[1] == "afr"
assert lang_longs[-1] == "Vietnamese"
```

#### `iter(lang_longs)` (`.__iter__()`)

Allows for anything that takes an `iter` to use `lang_2s`, `lang_3s`, or `lang_longs`.

```python
assert list(lang_2s) == [
    "ab",
    "af",
    ...
    "vi",
]
for lang in lang_longs:
    ...
```

#### `len(lang_2s)` (`.__len__()`)

```python
assert len(lang_2s) == 88
```
