from dataclasses import dataclass
from pathlib import Path

from subwinder.utils import special_hash


@dataclass
class Media:
    """
    Data container representing some media (Movie, Episode, etc.) to search for.
    """

    hash: str
    size: int
    dirname: Path
    filename: Path

    def __init__(self, filepath):
        """
        Builds a `Media` object from a local file.
        """
        filepath = Path(filepath)
        hash = special_hash(filepath)
        size = filepath.stat().st_size

        self._from_parts(hash, size)
        # Set file info from given `filepath`
        self.set_filepath(filepath)

    @classmethod
    def from_parts(cls, hash, size, dirname=None, filename=None):
        """
        Builds a `Media` object from the individual parts.
        """
        # Make a bare `Media` skipping the call to `__init__`
        media = cls.__new__(cls)
        media._from_parts(hash, size, dirname, filename)

        return media

    def _from_parts(self, hash, size, dirname=None, filename=None):
        self.hash = hash
        self.size = size
        self.set_dirname(dirname)
        self.set_filename(filename)

        return self

    def set_filepath(self, filepath):
        filepath = Path(filepath)

        self.set_filename(filepath.name)
        self.set_dirname(filepath.parent)

    def set_filename(self, filename):
        self.filename = None if filename is None else Path(filename)

    def set_dirname(self, dirname):
        self.dirname = None if dirname is None else Path(dirname)
