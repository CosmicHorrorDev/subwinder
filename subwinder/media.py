from dataclasses import dataclass
from pathlib import Path

from subwinder import hashers


@dataclass
class Media:
    hash: str
    size: int
    dirname: Path
    filename: Path

    def __init__(self, hash, size, dirname=None, filename=None):
        self.hash = hash
        self.size = size

        if dirname is not None:
            self.set_dirname(dirname)

        if filename is not None:
            self.set_filename(filename)

    @classmethod
    def from_file(cls, filepath):
        filepath = Path(filepath)
        hash = hashers.special_hash(filepath)
        size = filepath.stat().st_size

        media = cls(hash, size)
        # Set file info from given `filepath`
        media.set_filepath(filepath)
        return media

    def set_filepath(self, filepath):
        filepath = Path(filepath)

        self.set_filename(filepath.name)
        self.set_dirname(filepath.parent)

    def set_filename(self, filename):
        self.filename = Path(filename)

    def set_dirname(self, dirname):
        self.dirname = Path(dirname)
