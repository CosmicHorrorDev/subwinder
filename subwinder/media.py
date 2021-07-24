from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, cast

from subwinder.types import AnyPath
from subwinder.utils import special_hash


@dataclass
class MediaFile:
    """
    Data container representing some media (Movie, Episode, etc.) to search for.
    """

    hash: str
    size: int
    _dirname: Optional[Path]
    _filename: Optional[Path]

    def __init__(self, filepath: Path) -> None:
        """
        Builds a `MediaFile` object from a local file.
        """
        filepath = Path(filepath)
        hash = special_hash(filepath)
        size = filepath.stat().st_size

        self._from_parts(hash, size)
        # Set file info from given `filepath`
        self.set_filepath(filepath)

    @classmethod
    def from_parts(
        cls,
        hash: str,
        size: int,
        dirname: Optional[Path] = None,
        filename: Optional[Path] = None,
    ) -> MediaFile:
        """
        Builds a `MediaFile` object from the individual parts.
        """
        # Make a bare `MediaFile` skipping the call to `__init__`
        media = cls.__new__(cls)
        media._from_parts(hash, size, dirname, filename)

        return media

    def _from_parts(
        self,
        hash: str,
        size: int,
        dirname: Optional[Path] = None,
        filename: Optional[Path] = None,
    ) -> MediaFile:
        self.hash = hash
        self.size = size
        self.set_dirname(dirname)
        self.set_filename(filename)

        return self

    def set_filepath(self, filepath: Optional[AnyPath]) -> None:
        if filepath is None:
            self.set_filename(None)
            self.set_dirname(None)
        else:
            filepath = Path(filepath)

            self.set_filename(filepath.name)
            self.set_dirname(filepath.parent)

    def set_filename(self, filename: Optional[AnyPath]) -> None:
        self._filename = None if filename is None else Path(filename)

    def set_dirname(self, dirname: Optional[AnyPath]) -> None:
        self._dirname = None if dirname is None else Path(dirname)

    def get_filepath(self) -> Optional[Path]:
        filename = self.get_filename()
        dirname = self.get_dirname()

        if self.get_filename() is None or self.get_dirname() is None:
            return None

        filename = cast(Path, filename)
        dirname = cast(Path, dirname)

        return dirname / filename

    def get_filename(self) -> Optional[Path]:
        return self._filename

    def get_dirname(self) -> Optional[Path]:
        return self._dirname
