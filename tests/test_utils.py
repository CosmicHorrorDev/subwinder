import pytest

from subwinder.utils import extract, special_hash
from tests.utils import RandomTempFile

from subwinder.exceptions import SubHashError


def test_extract():
    COMPRESSED = (
        "H4sIAIXHxV0C/yXLwQ0CMQxE0VbmxoVCoAyzHiBS4lnFXtB2TyRuT/r6N/Yu1JuTV9wvY9EKL8mhTm"
        "wa+2QmHRYOxiZfzuNRrVZv8dQcVk3xP08dSMFps5/4WhRKSPvwBzf2OXZqAAAA"
    )
    IDEAL = (
        b"Hello there, I'm that good ole compressed and encoded subtitle information"
        b" that you so dearly want to save"
    )

    assert extract(COMPRESSED) == IDEAL


def test_special_hash():
    # Make sure fails on too small of size
    with RandomTempFile(128 * 1024 - 1) as rand_file:
        with pytest.raises(SubHashError):
            special_hash(rand_file)

    # Test for matching hashes
    HASHES = [
        "a7abc175960dcada",
        "25182dd38c3b3793",
        "51cbe0f797fcf0b2",
        "3a947b73b070ea20",
        "2503835efd3d3c59",
    ]
    for i, hash in zip(range(5), HASHES):
        with RandomTempFile(128 * 1024, seed=i) as rand_file:
            assert hash == special_hash(rand_file)
