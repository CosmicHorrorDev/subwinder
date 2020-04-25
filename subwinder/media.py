from dataclasses import dataclass
from pathlib import Path

from subwinder import hashers, utils


@dataclass
class Media:
    hash: str
    size: int
    dirname: Path
    filename: Path

    def __init__(self, hash, size, dirname=None, filename=None):
        self.hash = hash
        self.size = size
        self.dirname = None if dirname is None else self.set_dirname(dirname)
        self.filename = None if filename is None else self.set_filename(filename)

    @classmethod
    def from_file(cls, filepath):
        filepath = utils._force_path(filepath)
        hash = hashers.special_hash(filepath)
        size = filepath.stat().st_size

        return cls(hash, size, filepath)

    def set_filepath(self, filepath):
        filepath = utils._force_path(filepath)

        # Why does `Path().name` return a string??
        self.filename = Path(filepath.name)
        self.dirname = filepath.parent

    def set_filename(self, filename):
        self.filename = utils._force_path(filename)

    def set_dirname(self, dirname):
        self.dirname = utils._force_path(dirname)
