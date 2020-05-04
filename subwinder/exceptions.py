class SubwinderError(Exception):
    """
    This is the base exception that all the other custom exceptions are derived from.
    It's honestly just used when either something violates an assumption I made about
    the API.
    """


class SubLangError(SubwinderError):
    """
    Raised when the user tries to convert a language code using one of the global
    objects from `subwinder.lang` using an invalid value.
    """


class SubAuthError(SubwinderError):
    """
    Raised when trying to use `AuthSubwinder` without providing a username, password, or
    useragent. Or when the API returns a response indicating that user
    tried to perform an invalid action (401) or when the useragent isn't valid in some
    way (411, 414, 415).
    """


class SubUploadError(SubwinderError):
    """
    Raised if the user attempts to upload subtitles and the server returns a response
    for either invalid subtitles format (402) or internal subtitle validation failure
    (416).
    """


class SubDownloadError(SubwinderError):
    """
    Raised when the user tries to download subtitles in a way that needs either the
    directory name or media name without having been provided that information. Or this
    is raised when the user has reached the download limit.
    """


class SubServerError(SubwinderError):
    """
    When the server raises a 5xx error on a request or when the user hits more than 40
    requests in 10 seconds the library retries the request with exponential backoff for
    at least 10 seconds, but if that timeout is exceeded and the server is still
    returning either a 5xx or too many requests then a `SubServerError` is raised.
    """


class SubHashError(SubwinderError):
    """
    Raised when the user in some way tries to get the `subwinder.utils.special_hash` of
    a file that is below the minimum required size of 128 KiB.
    """


class SubLibError(SubwinderError):
    """
    Raised whenever there is an error based around the use of the library. This is
    primarily caused by invalid parameters getting passed through (no matter how strict
    I make most things).
    """
