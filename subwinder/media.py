from dataclasses import dataclass
import os

from subwinder import hashers


@dataclass
class Subtitles:
    hash: str

    def __init__(self, hash):
        self.hash = hash

    @classmethod
    def from_file(cls, filepath):
        return cls(hashers.md5_hash(filepath))


@dataclass
class Media:
    hash: str
    size: int
    dirname: str
    filename: str

    def __init__(self, hash, size, filepath=None):
        self.hash = hash
        self.size = size

        if filepath is None:
            self.dirname, self.filename = None, None
        else:
            self.dirname, self.filename = os.path.split(filepath)

    @classmethod
    def from_file(cls, filepath):
        hash = hashers.special_hash(filepath)
        size = os.path.getsize(filepath)

        return cls(hash, size, filepath)

    def set_filepath(self, filepath):
        self.dirname, self.filename = os.path.split(filepath)

    def set_filename(self, filename):
        self.filename = filename

    def set_dirname(self, dirname):
        self.dirname = dirname
