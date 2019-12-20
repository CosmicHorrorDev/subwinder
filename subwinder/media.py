import os

from subwinder import hashers


# TODO: to store filepath or not to store filepath, that is the question
class Subtitles:
    def __init__(self, filepath):
        self.hash = hashers.md5_hash(filepath)


class Movie:
    def __init__(self, hash, size, filepath=None):
        self.hash = hash
        self.size = size

        if filepath is None:
            self.file_dir, self.file_name = None, None
        else:
            self.file_dir, self.file_name = os.path.split(filepath)

    @classmethod
    def from_file(cls, filepath):
        hash = hashers.special_hash(filepath)
        size = os.path.getsize(filepath)

        return cls(hash, size, filepath)

    def set_file_name(self, file_name):
        self.file_name = file_name

    def set_file_dir(self, file_dir):
        self.file_dir = file_dir
