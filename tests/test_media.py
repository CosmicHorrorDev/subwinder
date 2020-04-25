from pathlib import Path

from subwinder.media import Media
from tests.constants import TEST_DIR


def test_Media():
    HASH_DIR = Path(TEST_DIR) / "hash_files"
    HASH_LOCATION = HASH_DIR / "random_1"
    media = Media.from_file(HASH_LOCATION)

    assert media.hash == "38516a7d01f4e37d"
    assert media.size == 128 * 1024
    assert media.filename == Path("random_1")
    assert media.dirname == HASH_DIR
