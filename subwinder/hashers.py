import os

from subwinder import utils


# TODO: to store filepath or not to store filepath, that is the question
class Subtitles:
    def __init__(self, filepath):
        self.hash = utils.md5_hash(filepath)


# TODO: to store filepath or not to store filepath, that is the question
class Movie:
    def __init__(self, filepath):
        self.hash = utils.special_hash(filepath)
        self.size = os.path.getsize(filepath)
