from pathlib import Path

from subwinder import Media
from tests.constants import TEST_DIR


def test_Media():
    HASH_DIR = Path(TEST_DIR) / "hash_files"
    HASH_LOCATION = HASH_DIR / "random_1"
    media = Media(HASH_LOCATION)

    assert media.hash == "38516a7d01f4e37d"
    assert media.size == 128 * 1024
    assert media.get_filename() == Path("random_1")
    assert media.get_dirname() == HASH_DIR
    assert media.get_filepath() == HASH_LOCATION
