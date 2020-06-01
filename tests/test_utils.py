from subwinder.utils import extract, special_hash
from tests.constants import TEST_DIR


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
    # Maps filename to hash
    hashes = {"random_1": "38516a7d01f4e37d", "random_2": "a16ad3dbbe8037fa"}

    for file, ideal_hash in hashes.items():
        hash = special_hash(TEST_DIR / "hash_files" / file)
        assert hash == ideal_hash
