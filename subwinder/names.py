from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, cast

from subwinder.exceptions import SubDownloadError
from subwinder.info import Subtitles
from subwinder.lang import LangFormat, lang_2s


# TODO: move all this once core is split up
# TODO: Having a formatter setup to indicate hearing impaired would be a good example of
# extending this. Would be good to see how easy it is to extend off `NameFormatter`
class BaseNameFormatter(ABC):
    @abstractmethod
    def generate(
        self,
        subtitles: Subtitles,
        media_filename: Optional[Path],
        media_dirname: Optional[Path],
        download_dir: Optional[Path],
    ) -> Path:
        pass


class NameFormatter(BaseNameFormatter):
    def __init__(self, name_format: str) -> None:
        self.name_format = name_format

    # TODO: is there some easy way to extend this or offer some of its functionality
    def generate(
        self,
        subtitles: Subtitles,
        media_filename: Optional[Path],
        media_dirname: Optional[Path],
        download_dir: Optional[Path],
    ) -> Path:
        # Make sure there is enough context to save subtitles
        if media_dirname is None and download_dir is None:
            # TODO: should be a TypeError or ValueError?
            raise SubDownloadError(
                "Insufficient context. Need to set either the `dirname` in"
                f" {subtitles} if possible or `download_dir` in"
                " `download_subtitles`"
            )

        if media_filename is None:
            # Hacky way to see if `media_name` is used in `name_format`
            try:
                _ = self.name_format.format(
                    lang_2="",
                    lang_3="",
                    lang_long="",
                    ext="",
                    upload_name="",
                    upload_filename="",
                )
            except KeyError:
                # Can't set the media's `media_name` if we have no `media_name`
                # TODO: should be a TypeError or ValueError?
                raise SubDownloadError(
                    "Insufficient context. Need to set the `filename` for"
                    f" {subtitles} if you plan on using `media_name` in the"
                    " `name_format`"
                )

        # Store the subtitle file next to the original media unless `download_dir`
        # was set
        if download_dir is None:
            dir_path = media_dirname
        else:
            dir_path = Path(download_dir)
        dir_path = cast(Path, dir_path)

        # Format the `filename` according to the `name_format` passed in
        upload_name = subtitles.filename.stem
        media_name = None if media_filename is None else media_filename.stem

        filename = self.name_format.format(
            media_name=media_name,
            lang_2=subtitles.lang_2,
            lang_3=lang_2s.convert(subtitles.lang_2, LangFormat.LANG_3),
            lang_long=lang_2s.convert(subtitles.lang_2, LangFormat.LANG_LONG),
            ext=subtitles.ext,
            upload_name=upload_name,
            upload_filename=subtitles.filename,
        )

        return dir_path / filename
