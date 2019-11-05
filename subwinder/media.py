import os

from subwinder import hashers


# TODO: to store filepath or not to store filepath, that is the question
class Subtitles:
    def __init__(self, filepath):
        self.hash = hashers.md5_hash(filepath)


class Movie:
    def __init__(self, filepath):
        self.hash = hashers.special_hash(filepath)
        self.size = os.path.getsize(filepath)
        self.filepath = filepath
