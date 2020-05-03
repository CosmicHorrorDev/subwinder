# Exceptions

All the custom exceptions used by used by the library are in the [`subwinder.exceptions`](#subwinderexceptions-module) module.

---

## Table of Contents

* [`subwinder.exceptions` module](#subwinderexceptions-module)
    * [`SubwinderError`](#subwindererror)
    * [`SubAuthError`](#subautherror)
    * [`SubDownloadError`](#subdownloaderror)
    * [`SubHashError`](#subhasherror)
    * [`SubLangError`](#sublangerror)
    * [`SubLibError`](#subliberror)
    * [`SubServerError`](#subservererror)
    * [`SubUploadError`](#subuploaderror)

---

## `subwinder.exceptions` module

This just contains the definitions for all the exceptions used by the library.

```python
from subwinder.exceptions import (
    SubwinderError,
    SubAuthError,
    SubDownloadError,
    SubHashError,
    SubLangError,
    SubLibError,
    SubServerError,
    SubUploadError,
)
```

### `SubwinderError`

This is the base exception that all the other custom exceptions are derived from. It's honestly just used when either something violates an assumption I made about the API or when the API returns a status code that I have no idea why it was raised. All of these places point back to raising an issue in this repo to try and address the issue.

### `SubAuthError`

Raised when trying to use [`AuthSubwinder`](Authenticated-Endpoints.md#authsubwinder) without providing a username, password, or useragent. Or this is raised when the API returns a response indicating that user tried to perform an invalid action (401) or when the useragent isn't valid in some way (411, 414, 415).

```python
from subwinder.auth import AuthSubwinder

import os


# Username isn't provided in environment variables
assert "OPEN_SUBTITLES_USERNAME" not in os.environ
# nor is it given when creating the `AuthSubwinder` so `SubAuthError` is raised
with AuthSubwinder() as asw:
    ...
```

### `SubDownloadError`

Raised when the user tries to download subtitles in a way that needs either the directory name or media name without having been provided that information. Or this is raised when the user has reached the download limit.

### `SubHashError`

Raised when the user in some way tries to get the `subwinder.utils.special_hash` of a file that is below the minimum required size of 128 KiB.

```python
from subwinder.media import Media

import os


# File is below the minimum size
assert os.path.size("/some/file.mkv") < 128 * 1024
# This would raise a `SubHashError` since it indirectly uses `special_hash`
media = Media.from_file("/some/file.mkv")
```

### `SubLangError`

Raised when the user tries to convert a language code using one of the global objects from `subwinder.lang` using an invalid value.

```python
from subwinder.lang import LangFormat, lang_longs


# Raises a `SubLangError` since there was no matching language
lang_2 = lang_longs.convert("Gibberish", LangFormat.LANG_2)
```

### `SubLibError`

Raised whenever there is an error based around the use of the library. This is primarily caused by invalid parameters getting passed through (no matter how strict I make most things).

```python
from Subwinder.auth import AuthSubwinder


with AuthSubwinder("<username>", "<password>", "<useragent>") as asw:
    # Example: Raises a `SubLibError` when trying to update using an invalid
    #          program name
    asw.auto_update("Program that doesn't actually exist")
```

### `SubServerError`

When the server raises a 5xx error on a request or when the user hits more than 40 requests in 10 seconds the library retries the request with exponential backoff for at least 10 seconds, but if that timeout is exceeded and the server is still returning one a 5xx or too many requests then a `SubServerError` is raised.

### `SubUploadError`

Raised if the user attempts to upload subtitles and the server returns a response for either invalid subtitles format (402) or internal subtitle validation failure (416).
