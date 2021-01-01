from pathlib import Path

from subwinder.exceptions import SubDownloadError
from subwinder.lang import LangFormat, lang_2s


# TODO: move all this once core is split up
class BaseNameFormatter:
    def generate(self, sub_container, media_filename, media_dirname, download_dir):
        raise NotImplementedError(
            "The base formatter is only meant to be inherited from to ensure structure"
        )


class NameFormatter:
    def __init__(self, name_format):
        self.name_format = name_format

    def generate(self, sub_container, media_filename, media_dirname, download_dir):
        # Make sure there is enough context to save subtitles
        if media_dirname is None and download_dir is None:
            # TODO: should be a TypeError or ValueError?
            raise SubDownloadError(
                "Insufficient context. Need to set either the `dirname` in"
                f" {sub_container} if possible or `download_dir` in"
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
                    f" {sub_container} if you plan on using `media_name` in the"
                    " `name_format`"
                )

        # Store the subtitle file next to the original media unless `download_dir`
        # was set
        if download_dir is None:
            dir_path = media_dirname
        else:
            dir_path = Path(download_dir)

        # Format the `filename` according to the `name_format` passed in
        upload_name = sub_container.filename.stem
        media_name = None if media_filename is None else media_filename.stem

        filename = self.name_format.format(
            media_name=media_name,
            lang_2=sub_container.lang_2,
            lang_3=lang_2s.convert(sub_container.lang_2, LangFormat.LANG_3),
            lang_long=lang_2s.convert(sub_container.lang_2, LangFormat.LANG_LONG),
            ext=sub_container.ext,
            upload_name=upload_name,
            upload_filename=sub_container.filename,
        )

        return dir_path / filename
