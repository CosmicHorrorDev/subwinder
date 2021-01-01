#!/usr/bin/env python
import json
from itertools import repeat
from pathlib import Path

from subwinder import AuthSubwinder, MediaFile, info
from subwinder.exceptions import SubHashError
from subwinder.names import NameFormatter
from subwinder.ranking import rank_search_subtitles


def main():
    # Setting up some of the constants for our program
    # Directory that we're scanning from and moving to
    INPUT_DIR = Path("/path/to/input/dir")
    OUTPUT_DIR = Path("/path/to/output/dir")
    # Whitelist used for our custom ranking function
    AUTHOR_WHITELIST = ["john", "jacob", "jingleheimer", "schmidt"]
    # Our preferred sub extensions
    SUB_EXTS = ["ssa", "ass", "srt"]
    # File that we're storing all our saved subtitles info in for later in case you
    # want to rebuild any of the results from it and comment/vote/report them
    SAVED_SUBS_FILE = Path("/path/to/ledger.json")
    # The language we want to search for
    LANG = "en"

    adv_quickstart(
        INPUT_DIR, OUTPUT_DIR, SAVED_SUBS_FILE, LANG, AUTHOR_WHITELIST, SUB_EXTS
    )


def adv_quickstart(input_dir, output_dir, ledger, lang, author_whitelist, sub_exts):
    # So now let's get all the files in `INPUT_DIR` as `MediaFile` objects
    print(f"Scanning {input_dir}... ", end="")
    media = []
    for item in input_dir.glob("**/*"):
        # We only care about files
        if item.is_file():
            # Hashing can fail if the file is too small (under 128 KiB)
            try:
                media.append(MediaFile(item))
            except SubHashError:
                pass
    print(f"Found {len(media)} files")

    # And now onto using the API, so I'm going to assume that all the credentials are
    # set with `OPEN_SUBTITLES_USERNAME`, `OPEN_SUBTITLES_PASSWORD`, and
    # `OPEN_SUBTITLES_USERAGENT`, but you can pass them as params to `AuthSubwinder` too
    with AuthSubwinder() as asw:
        # Now we can search for all of our `media` using our custom ranking function
        print("Searching... ", end="")
        results = asw.search_subtitles(
            zip(media, repeat(lang)),
            custom_rank_func,
            author_whitelist,
            sub_exts,
        )
        # Filter out items that didn't get any matches
        results = [result for result in results if result is not None]
        print(f"Found {len(results)} matches")

        # Your number of downloads from the API are on a daily limit so slice our
        # desired number of downloads to the max
        results = results[: asw.daily_download_info().remaining]
        print(f"Downloading {len(results)} subtitles... ", end="")
        download_paths = asw.download_subtitles(
            results, name_formatter=NameFormatter("{media_name}.{lang_3}.{ext}")
        )
        print("Downloaded")
    # And at this point we're done with the API. Exiting the `with` logs out of the API

    # Move all the media that we have subtitles for now
    # Note: that this does not retain any special directory structure from
    #       `INPUT_DIR` in `OUTPUT_DIR`
    print(f"Moving matched media and subtitle files to {output_dir}... ", end="")
    output_dir.mkdir(exist_ok=True, parents=True)
    for result, download in zip(results, download_paths):
        from_media_path = result.media.get_filepath()
        to_media_path = output_dir / from_media_path.name
        from_media_path.rename(to_media_path)

        from_sub_path = download
        to_sub_path = output_dir / from_sub_path.name
        from_sub_path.rename(to_sub_path)
    print("Moved")

    # Save the search results to a file in case we want them later
    print(f"Updating index of saved files {ledger}... ", end="")
    if ledger.is_file():
        with ledger.open() as file:
            saved_subs = json.load(file)
    else:
        saved_subs = []

    ext_subs = [ExtSubtitles.from_subtitles(result) for result in results]
    saved_subs += [ext_sub.to_json_dict() for ext_sub in ext_subs]

    with ledger.open("w") as file:
        json.dump(saved_subs, file)
    print("Updated")


# Lets setup our custom ranking function
# Prefer `rank_by_whitelist` and keep the default ranking function as a fallback
def custom_rank_func(results, query, author_whitelist, sub_exts=None):
    return (
        rank_by_whitelist(results, query, author_whitelist)
        # Fallback to default ranking, but we decide not to `exclude_bad`
        or rank_search_subtitles(results, query, exclude_bad=False, sub_exts=sub_exts)
    )


def rank_by_whitelist(results, query, author_whitelist):
    # Search all the results for a known-good author
    for result in results:
        # Author can be `None` if the subtitles were anonymously uploaded
        if result.author is not None:
            if result.author.name in author_whitelist:
                return result

    # No matching result
    return None


# So the reason storing this makes sense is that there is no way to go from a local
# subtitle file to the id for it on opensubtitles, so if you're doing anything with
# the result later (commenting on it, etc.) you would want to store the attributes.
# And yes you can just pickle the `Subtitles`. This is really just showing off that you
# can extend `Subtitles` while still using it in places that expect a `Subtitles`
# (maybe you're storing and retrieving the information from a database or something).
class ExtSubtitles(info.Subtitles):
    @classmethod
    def from_subtitles(cls, sub_container):
        # Add the option for passing `SearchResults` in
        if isinstance(sub_container, info.SearchResult):
            sub_container = sub_container.subtitles

        # We just want all the members from `sub_container` in our `ExtSubtitles`
        # Yes this seems hacky, python's classes are _interesting_, so were going to
        # create a `ExtSubtitles` skipping `__init__` by using `__new__` then set
        # our members (aka `__dict__`) to all of those from `subtitles`
        ext_subtitles = ExtSubtitles.__new__(ExtSubtitles)
        ext_subtitles.__dict__ = sub_container.__dict__
        return ext_subtitles

    def to_json_dict(self):
        # Need to get everything into a `dict` of json serializable values
        json_dict = self.__dict__
        json_dict["filename"] = str(self.filename)

        return json_dict

    @classmethod
    def from_json_dict(cls, json_dict):
        # And now we just need to do the reverse of `.to_json_dict(...)`
        subtitles = info.Subtitles.__new__(info.Subtitles)
        subtitles.filename = Path(subtitles.filename)

        # Now return the `ExtSubtitles` for our `Subtitles`
        return ExtSubtitles.from_subtitles(subtitles)


if __name__ == "__main__":
    main()
