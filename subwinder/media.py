import os

from subwinder import hashers


# TODO: to store filepath or not to store filepath, that is the question
class Subtitles:
    def __init__(self, filepath):
        self.hash = hashers.md5_hash(filepath)


class Movie:
    def __init__(self, hash, size, filepath):
        self.hash = hash
        self.size = size
        self.filepath = filepath

    @classmethod
    def from_file(cls, filepath):
        hash = hashers.special_hash(filepath)
        size = os.path.getsize(filepath)

        return cls(hash, size, filepath)
