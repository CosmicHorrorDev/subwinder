"""
I just wanted the option to have some tests run by default, but I couldn't find anything
documented for it, so enjoy this pytest black magic.
"""

import pytest


def pytest_addoption(parser):
    # Add a command line option to run all tests
    parser.addoption(
        "--run-all",
        action="store_true",
        help="Run all tests (some are skipped by default because they're slow)",
    )


@pytest.fixture(autouse=True)
def skip_non_default(request, pytestconfig):
    node = request.node
    run_all = request.config.getoption("--run-all")

    # Skip any tests that have a marker set
    if not run_all and node.own_markers:
        pytest.skip(
            f"Skipping mark for reason {node.own_markers[0].name}. Run with option"
            " --run-all to run this"
        )
