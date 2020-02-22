from datetime import datetime
import time
from xmlrpc.client import ServerProxy, Transport

from subwinder.constants import _API_BASE, _REPO_URL
from subwinder.exceptions import (
    SubAuthError,
    SubDownloadError,
    SubLibError,
    SubServerError,
    SubUploadError,
)


# Responses 403, 404, 405, 406, 409 should be prevented by API
_API_ERROR_MAP = {
    "401": SubAuthError,
    "402": SubUploadError,
    "407": SubDownloadError,
    "408": SubLibError,
    "410": SubLibError,
    "411": SubAuthError,
    "412": SubUploadError,
    "413": SubLibError,
    "414": SubAuthError,
    "415": SubAuthError,
    "416": SubUploadError,
    "429": SubServerError,
    "503": SubServerError,
    "506": SubServerError,
    "520": SubServerError,
}

_client = ServerProxy(_API_BASE, allow_none=True, transport=Transport())


# FIXME: Handle xmlrpc.client.ProtocolError, 503, 506, and 520  are raised as protocol
#        errors. Catch and manually change status
# TODO: give a way to let lib user to set `TIMEOUT`?
def _request(method, token, *params):
    TIMEOUT = 15
    DELAY_FACTOR = 2
    current_delay = 1.5
    start = datetime.now()

    while True:
        if method in ("AutoUpdate", "GetSubLanguages", "LogIn", "ServerInfo"):
            # Flexible way to call method while reducing error handling
            resp = getattr(_client, method)(*params)
        else:
            # Use the token if it's defined
            resp = getattr(_client, method)(token, *params)

        # All requests return a status except for GetSubLanguages and ServerInfo
        if method in ("GetSubLanguages", "ServerInfo"):
            return resp

        if "status" not in resp:
            raise SubLibError(
                f'"{method}" should return a status and didn\'t, consider raising an'
                f" issue at {_REPO_URL} to address this"
            )

        status_code = resp["status"][:3]
        status_msg = resp["status"][4:]

        # Retry if 429 or 503, otherwise handle appropriately
        # FIXME: 503 fails the request so it won't be passed in this way instead catch
        #        the error and manually set a status
        if status_code not in ("429", "503"):
            break

        # Server under heavy load, wait and retry
        remaining_time = TIMEOUT - (datetime.now() - start).total_seconds()
        if remaining_time <= current_delay:
            # Not enough time to try again so go ahead and `break`
            break

        time.sleep(current_delay)
        current_delay *= DELAY_FACTOR

    # Handle the response
    if status_code == "200":
        return resp
    elif status_code in _API_ERROR_MAP:
        raise _API_ERROR_MAP[status_code](status_msg)
    else:
        raise SubLibError(
            "the API returned an unhandled response, consider raising an issue to"
            f" address this at {_REPO_URL}\nResponse status: '{resp['status']}'"
        )
