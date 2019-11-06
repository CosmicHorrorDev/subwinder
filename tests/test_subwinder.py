from subwinder import __version__
from subwinder.exceptions import SubAuthError
from subwinder.lib import AuthSubWinder

import pytest


def test_version():
    assert __version__ == "0.1.0"


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
