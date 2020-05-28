#!/usr/bin/env python
from subwinder import info, AuthSubwinder

from datetime import datetime as dt
import sys


def main():
    LANG = "en"

    # Assumes all the credentials are set using environment variables
    with AuthSubwinder() as asw:
        # Give a nice friendly prompt
        user_info = asw.user_info()
        download_info = asw.daily_download_info()
        print(
            f"Hello {user_info.name}, you have {download_info.remaining} of"
            f" {download_info.limit} downloads remaining for the day!\n"
        )

        # Search for some media
        query = input("What media do you want to find subtitles for? ")
        media = asw.suggest_media(query)

        # Build our extended objects and display the media
        ext_media = [build_extended_mediainfo(m) for m in media]
        for i, media in enumerate(ext_media):
            print(f"{i}) {media}")
        print()

        # Find which one they want to view
        resp = int(input(f"Which do you want to see? (0 -> {len(ext_media) - 1}) "))
        if resp < 0 or resp >= len(ext_media):
            sys.exit(f"Entry {resp} out of bounds (0 -> {len(ext_media) - 1})")

        # Search for the subtitles
        desired = ext_media[resp]
        # This is the special case of a `TvSeriesInfo` again. So if we have a
        # `TvSeriesInfo` we need to get the specific episode to search for. If you have
        # information about the number of series and episodes available then you could
        # search for all of them at once too
        if type(desired) == ExtTvSeriesInfo:
            print("It looks like you selected a tv series!")
            season = int(input("What season do you want? "))
            episode = int(input("What episode do you want? "))
            print()
            desired = info.EpisodeInfo.from_tv_series(desired, season, episode)
        results = asw.search_subtitles_unranked([(desired, LANG)])[0]
        ext_results = [ExtSearchResult.from_search_result(result) for result in results]

        print("Results:")
        for i, ext_result in enumerate(ext_results):
            print(f"{i}) {ext_result}")
        print()

        resp = int(
            input(f"Which one do you want to preview? (0 -> {len(ext_results) - 1}) ")
        )
        if resp < 0 or resp >= len(ext_results):
            sys.exit(f"Entry {resp} out of bounds (0 -> {len(ext_results) - 1})")
        result = ext_results[resp]
        preview = asw.preview_subtitles([result])[0]
        # Limit preview size
        print(f"Preview: {preview[:200]}\n")

        resp = input("Do you want to download these subtitles? (Y/n) ").strip().lower()
        if resp == "n":
            sys.exit()
        elif resp not in ["y", ""]:
            sys.exit(f"Unrecognized option '{resp}'")

        resp = input("Where do you want them downloaded? ")

        download_path = asw.download_subtitles([result], download_dir=resp)[0]
        print(f"Downloaded to '{download_path}', have a nice day!")


# And now we can extend all the `MediaInfo` classes we care about
class ExtMovieInfo(info.MediaInfo):
    def __str__(self):
        return f"(Movie)\t{self.name}\t({self.year})\t(imdb: {self.imdbid})"


class ExtTvSeriesInfo(info.TvSeriesInfo):
    def __str__(self):
        return f"(TV Series)\t{self.name}\t({self.year})\t(imdb: {self.imdbid})"


# Helper function to make it easier to build the appropriate extended `MediaInfo`
def build_extended_mediainfo(obj):
    CLASS_MAP = {
        info.MovieInfo: ExtMovieInfo,
        info.TvSeriesInfo: ExtTvSeriesInfo,
    }

    # Skip the constructor and add all the members since they should be the same
    class_type = CLASS_MAP[type(obj)]
    ext_media = class_type.__new__(class_type)
    ext_media.__dict__ = obj.__dict__

    return ext_media


class ExtSearchResult(info.SearchResult):
    TIME_FMT = "%Y-%m-%d %H:%M:%S"

    @classmethod
    def from_search_result(cls, search_result):
        ext_result = ExtSearchResult.__new__(ExtSearchResult)
        ext_result.__dict__ = search_result.__dict__

        return ext_result

    def __str__(self):
        upload = dt.strftime(self.upload_date, self.TIME_FMT)
        sub = self.subtitles
        author = "NA" if self.author is None else self.author.name
        return f"[{upload} | by {author} | {sub.ext}] {sub.filename}"


if __name__ == "__main__":
    main()
