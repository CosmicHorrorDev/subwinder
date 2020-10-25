"""
I just wanted the option to have some tests run by default, but I couldn't find anything
documented for it, so enjoy this pytest black magic.
"""

import pytest

from datetime import datetime as dt

from subwinder.lang import _converter


def pytest_addoption(parser):
    # Add a command line option to run all tests
    parser.addoption(
        "--run-all",
        action="store_true",
        help="Run all tests (some are skipped by default because they're slow)",
    )


@pytest.fixture(autouse=True)
def _skip_non_default(request):
    node = request.node

    # IF we are skipping non default and we have a mark
    # TODO: check for specific mark values
    if skip_non_default(request) and request.node.own_markers:
        pytest.skip(
            f"Skipping mark for reason {node.own_markers[0].name}. Run with option"
            " --run-all to run this"
        )


def skip_non_default(request):
    run_all = request.config.getoption("--run-all")
    mark = request.config.getoption("-m")

    # skip tests if mark value isn't given and run all is not specified
    return not mark and not run_all


@pytest.fixture(autouse=True)
def _fake_langs():
    stored = _converter.dump()
    _converter.set(
        dt.now(),
        [["de", "en", "fr"], ["ger", "eng", "fre"], ["German", "English", "French"]],
    )

    yield

    _converter.set(*stored)


# Negates `_fake_langs` which by default fakes the language listing
@pytest.fixture
def no_fake_langs():
    stored = _converter.dump()

    yield

    _converter.set(*stored)
