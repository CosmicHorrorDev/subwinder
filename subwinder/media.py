from dataclasses import dataclass
from pathlib import Path

from subwinder import hashers, utils


@dataclass
class Subtitles:
    hash: str

    def __init__(self, hash):
        self.hash = hash

    @classmethod
    def from_file(cls, filepath):
        filepath = utils._force_path(filepath)
        return cls(hashers.md5_hash(filepath))


@dataclass
class Media:
    hash: str
    size: int
    dirname: Path
    filename: Path

    # TODO: why not split up the dirname and filename for this?
    def __init__(self, hash, size, filepath=None):
        self.hash = hash
        self.size = size

        if filepath is None:
            self.dirname, self.filename = None, None
        else:
            self.set_filepath(filepath)

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
