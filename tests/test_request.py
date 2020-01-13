from unittest.mock import call, patch

from subwinder.request import _client, _request


# Note: this test takes a bit of time because of the delayed API request retry
def test__request():
    RESP = {"status": "200 OK", "data": "The data!", "seconds": "0.15"}
    with patch.object(_client, "ServerInfo", return_value=RESP) as mocked:
        # Response should be passed through on success
        assert _request("ServerInfo", None) == RESP
        mocked.assert_called_once_with()

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
        assert _request("GetUserInfo", "<token>", "arg1", "arg2") == RESPS[1]
        mocked.assert_has_calls(CALLS)
