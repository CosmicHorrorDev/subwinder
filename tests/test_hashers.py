import subwinder.hashers

import os


def test_special_hash():
    # Maps filename to hash
    hashes = {"random_1": "38516a7d01f4e37d", "random_2": "a16ad3dbbe8037fa"}

    tests_dir = os.path.dirname(__file__)
    for file, ideal_hash in hashes.items():
        hash = subwinder.hashers.special_hash(
            os.path.join(tests_dir, "hash_files", file)
        )
        assert hash == ideal_hash


def test_md5_hash():
    """
    Same concept as `test_special_hash`, but with md5 hash instead
    """
    hashes = {
        "random_1": "52b16cb071a2da214782380a0100003b",
        "random_2": "f6eef93deb14c19ded05f76a17928b21",
    }

    tests_dir = os.path.dirname(__file__)
    for file, ideal_hash in hashes.items():
        hash = subwinder.hashers.md5_hash(
            os.path.join(tests_dir, "hash_files", file)
        )
        assert hash == ideal_hash
