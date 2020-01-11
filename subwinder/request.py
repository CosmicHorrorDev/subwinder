from datetime import datetime
import time
from xmlrpc.client import ServerProxy, Transport

from subwinder.constants import _API_BASE, _REPO_URL
from subwinder.exceptions import (
    SubAuthError,
    SubDownloadError,
    SubWinderError,
    SubServerError,
    SubUploadError,
)


# Responses 403, 404, 405, 406, 409 should be prevented by API
_API_ERROR_MAP = {
    "401": SubAuthError,
    "402": SubUploadError,
    "407": SubDownloadError,
    "408": SubWinderError,
    "410": SubWinderError,
    "411": SubAuthError,
    # TODO: is this an upload error?
    "412": SubWinderError,
    "413": SubWinderError,
    "414": SubAuthError,
    "415": SubAuthError,
    "416": SubUploadError,
    "429": SubServerError,
    "503": SubServerError,
    "506": SubServerError,
    "520": SubServerError,
}

_client = ServerProxy(_API_BASE, allow_none=True, transport=Transport())


# FIXME: Handle xmlrpc.client.ProtocolError, 503 and 506 are raised as
#        protocol errors, change to allow for this
#        Also occurs for 520 which isn't listed
# TODO: give a way to let lib user to set `TIMEOUT`?
def _request(method, token, *params):
    TIMEOUT = 15
    DELAY_FACTOR = 2
    current_delay = 1.5
    start = datetime.now()

    while (datetime.now() - start).total_seconds() <= TIMEOUT:
        if method in ("GetSubLanguages", "LogIn", "ServerInfo"):
            # Flexible way to call method while reducing error handling
            resp = getattr(_client, method)(*params)
        else:
            # Use the token if it's defined
            resp = getattr(_client, method)(token, *params)

        # All requests return a status except for GetSubLanguages and
        # ServerInfo
        if method in ("GetSubLanguages", "ServerInfo"):
            return resp

        if "status" not in resp:
            raise SubWinderError(
                f'"{method}" should return a status and didn\'t, consider'
                f" raising an issue at {_REPO_URL}"
            )

        status_code = resp["status"][:3]
        status_msg = resp["status"][4:]

        # Retry if 429 or 503, otherwise handle appropriately
        # FIXME: 503 fails the request so it won't be passed in this way
        #        instead catch the error and manually set a status
        if status_code not in ("429", "503"):
            break

        # Server under heavy load, wait and retry
        remaining_time = TIMEOUT - (datetime.now() - start).total_seconds()
        if remaining_time > current_delay:
            time.sleep(current_delay)
        else:
            # Not enough time to try again so go ahead and `break`
            break

        current_delay *= DELAY_FACTOR

    # Handle the response
    if status_code == "200":
        return resp
    elif status_code in _API_ERROR_MAP:
        raise _API_ERROR_MAP[status_code](status_msg)
    else:
        raise SubWinderError(
            "the API returned an unhandled response, consider raising an"
            f" issue to address this at {_REPO_URL}"
            f"\nResp: {status_code}: {status_msg}"
        )
