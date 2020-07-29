from unittest.mock import call, patch
from multiprocessing.dummy import Pool
from datetime import datetime as dt

from subwinder._request import _client, request, Endpoints
from subwinder.exceptions import SubServerError

import pytest


def test__request():
    RESP = {"status": "200 OK", "data": "The data!", "seconds": "0.15"}
    with patch.object(_client, "ServerInfo", return_value=RESP) as mocked:
        # Response should be passed through on success
        assert request(Endpoints.SERVER_INFO, None) == RESP
        mocked.assert_called_once_with()


# Note: this test takes a bit of time because of the delayed API request retry
@pytest.mark.slow
def test_retry_on_fail():
    CALLS = [
        call("<token>", "arg1", "arg2"),
        call("<token>", "arg1", "arg2"),
    ]
    RESPS = [
        {"status": "429 Too many requests", "seconds": "0.10"},
        {"status": "200 OK", "data": "The data!", "seconds": "0.15"},
    ]
    with patch.object(_client, "GetUserInfo") as mocked:
        mocked.side_effect = RESPS
        assert request(Endpoints.GET_USER_INFO, "<token>", "arg1", "arg2") == RESPS[1]
        mocked.assert_has_calls(CALLS)


@pytest.mark.slow
def test_request_timeout():
    # Requests take a bit to timeout so were just gonna run all of them simulatneously
    with Pool(len(Endpoints)) as pool:
        pool.map(_test_request_timeout, list(Endpoints))


def _test_request_timeout(endpoint):
    RATE_LIMIT_SECONDS = 10

    # Due to the exponential backoff this should be enough errors to trigger a timeout
    RESPS = [
        {"status": "429 Too many requests", "seconds": "0.10"},
        {"status": "429 Too many requests", "seconds": "0.10"},
        {"status": "429 Too many requests", "seconds": "0.10"},
        {"status": "429 Too many requests", "seconds": "0.10"},
    ]

    # XXX: does calling a patched object several times just return the same response
    #      already?
    with patch.object(_client, endpoint.value) as mocked:
        mocked.side_effect = RESPS
        start = dt.now()
        with pytest.raises(SubServerError):
            request(endpoint, "<token>")

        # `request` should keep trying long enough for the rate limit to expire
        assert (dt.now() - start).total_seconds() > RATE_LIMIT_SECONDS
