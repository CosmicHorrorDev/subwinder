from subwinder import __version__
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
