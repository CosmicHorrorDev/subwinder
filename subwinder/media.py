import os

from subwinder import hashers
from subwinder.utils import auto_repr


# TODO: to store filepath or not to store filepath, that is the question
#       see how this gets used first
@auto_repr
class Subtitles:
    def __init__(self, hash):
        self.hash = hash

    @classmethod
    def from_file(cls, filepath):
        hash = hashers.md5_hash(filepath)

        return cls(hash)


@auto_repr
class Movie:
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

    def set_filename(self, filename):
        self.filename = filename

    def set_dirname(self, dirname):
        self.dirname = dirname
