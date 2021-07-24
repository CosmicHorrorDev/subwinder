import warnings
from pathlib import Path

from dev.fake_media.fake_media import (
    fake_media,
    validate_sparse_support,
    write_sparse_file,
)
from subwinder import MediaFile
from tests.constants import DEV_ASSETS


def test_validate_sparse_support(tmp_path):
    if not validate_sparse_support(tmp_path):
        warnings.warn(
            "Not able to verify sparse file support. It's possible that this system"
            " supports sparse files, but is not able to determine the actual file size"
            " on disk to know (Windows specifically uses FSUtil to create the sparse"
            " file, but I can't find how to find the actual size on disk). This should"
            " work on most Unix-likes and Mac, although I'm not sure about FreeBSD."
        )


# TODO: can we test through to arg parsing too?
def test_fake_media(tmp_path):
    IDEAL = [
        MediaFile.from_parts(
            "0123456789abcdef", 1234567, tmp_path, Path("File 1.dummy")
        ),
        MediaFile.from_parts(
            "00000000deadbeef", 333333, tmp_path, Path("File 2.dummy")
        ),
    ]
    DUMMY_ENTRY_FILE = DEV_ASSETS / "fake_media" / "dummy_entries.json"

    # Generate the dummy dummy files and check that they look right
    fake_media(DUMMY_ENTRY_FILE, tmp_path)
    real = [
        MediaFile(tmp_path / "File 1.dummy"),
        MediaFile(tmp_path / "File 2.dummy"),
    ]

    assert real == IDEAL


def test_write_sparse_file(tmp_path):
    filepath = tmp_path / "Test.file"
    occupied_contents = b"Null -> "
    write_sparse_file(filepath, occupied_contents, len(occupied_contents) + 1)

    with filepath.open("rb") as file:
        assert file.read() == occupied_contents + b"\0"
