from subwinder.exceptions import SubAuthError
from subwinder.auth import AuthSubWinder

import pytest


def test_authsubwinder_init():
    bad_params = [
        # Missing both username and password
        ["<useragent"],
        # Missing password
        ["<useragent>", "<username>"],
        # Invalid useragent
        [None, "<username>", "<password>"],
    ]

    for params in bad_params:
        with pytest.raises(SubAuthError):
            AuthSubWinder(*params)
