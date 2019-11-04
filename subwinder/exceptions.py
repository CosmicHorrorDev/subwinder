class SubWinderError(Exception):
    pass


# FIXME: this is unused
class SubLangError(SubWinderError):
    pass


class SubAuthError(SubWinderError):
    pass


class SubUploadError(SubWinderError):
    pass


class SubDownloadError(SubWinderError):
    pass


# FIXME: this is unused
class SubServerError(SubWinderError):
    pass


class SubHashError(SubWinderError):
    pass
