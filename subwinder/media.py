from dataclasses import dataclass
from pathlib import Path

from subwinder import hashers, _internal_utils


@dataclass
class Media:
    hash: str
    size: int
    dirname: Path
    filename: Path

    def __init__(self, hash, size, dirname=None, filename=None):
        self.hash = hash
        self.size = size

        self.set_dirname(dirname)
        self.set_filename(filename)

    @classmethod
    def from_file(cls, filepath):
        filepath = _internal_utils.force_path(filepath)
        hash = hashers.special_hash(filepath)
        size = filepath.stat().st_size

        media = cls(hash, size)
        # Set file info from given `filepath`
        media.set_filepath(filepath)
        return media

    def set_filepath(self, filepath):
        filepath = _internal_utils.force_path(filepath)

        # Why does `Path().name` return a string??
        self.filename = Path(filepath.name)
        self.dirname = filepath.parent

    def set_filename(self, filename):
        self.filename = _internal_utils.force_path(filename)

    def set_dirname(self, dirname):
        self.dirname = _internal_utils.force_path(dirname)
