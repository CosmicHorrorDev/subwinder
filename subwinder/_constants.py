from enum import Enum

API_BASE = "https://api.opensubtitles.org/xml-rpc"

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

REPO_URL = "https://github.com/LovecraftianHorror/subwinder"

DEV_USERAGENT = "TemporaryUserAgent"


class Env(Enum):
    USERAGENT = "OPEN_SUBTITLES_USERAGENT"
    USERNAME = "OPEN_SUBTITLES_USERNAME"
    PASSWORD = "OPEN_SUBTITLES_PASSWORD"
    PASSWORD_HASH = "OPEN_SUBTITLES_MD5_PASSWORD_HASH"
