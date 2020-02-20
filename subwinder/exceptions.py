class SubwinderError(Exception):
    pass


class SubLangError(SubwinderError):
    pass


class SubAuthError(SubwinderError):
    pass


class SubUploadError(SubwinderError):
    pass


class SubDownloadError(SubwinderError):
    pass


class SubServerError(SubwinderError):
    pass


class SubHashError(SubwinderError):
    pass


class SubLibError(SubwinderError):
    pass
