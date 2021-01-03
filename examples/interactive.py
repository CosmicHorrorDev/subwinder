#!/usr/bin/env python
from datetime import datetime as dt

from subwinder import AuthSubwinder, info


def main():
    # Language of our desired subtitles
    LANG = "en"
    interative(LANG)


def interative(lang):
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
        ext_media = [build_extended_media(m) for m in media]
        for i, media in enumerate(ext_media):
            print(f"{i}) {media}")
        print()

        # Find which one they want to view
        resp = int(input(f"Which do you want to see? (0 -> {len(ext_media) - 1}) "))
        if resp < 0 or resp >= len(ext_media):
            raise OutOfBoundsError(
                f"Entry {resp} out of bounds (0 -> {len(ext_media) - 1})"
            )

        # Search for the subtitles
        desired = ext_media[resp]
        # This is the special case of a `TvSeries` again. So if we have a
        # `TvSeries` we need to get the specific episode to search for. If you have
        # information about the number of series and episodes available then you could
        # search for all of them at once too
        if type(desired) == ExtTvSeries:
            print("It looks like you selected a tv series!")
            season = int(input("What season do you want? "))
            episode = int(input("What episode do you want? "))
            print()
            desired = info.Episode.from_tv_series(desired, season, episode)
        results = asw.search_subtitles_unranked([(desired, lang)])[0]
        ext_results = [ExtSearchResult(result) for result in results]

        print("Results:")
        for i, ext_result in enumerate(ext_results):
            print(f"{i}) {ext_result}")
        print()

        resp = int(
            input(f"Which one do you want to preview? (0 -> {len(ext_results) - 1}) ")
        )
        if resp < 0 or resp >= len(ext_results):
            raise OutOfBoundsError(
                f"Entry {resp} out of bounds (0 -> {len(ext_results) - 1})"
            )
        result = ext_results[resp]
        preview = asw.preview_subtitles([result])[0]
        # Limit preview size
        print(f"Preview:\n{preview[:200]}\n")

        resp = input("Do you want to download these subtitles? (Y/n) ").strip().lower()
        if resp == "n":
            return
        elif resp not in ["y", ""]:
            raise BadResponseError(f"Unrecognized option '{resp}'")

        resp = input("Where do you want them downloaded? ")

        download_path = asw.download_subtitles([result], download_dir=resp)[0]
        print(f"Downloaded to '{download_path}', have a nice day!")


# And now we can extend all the `Media` classes we care about
class ExtMovie(info.Movie):
    def __init__(self, movie):
        super().__init__(
            movie.name,
            movie.year,
            movie.imdbid,
            movie.get_dirname(),
            movie.get_filename(),
        )

    def __str__(self):
        return f"(Movie)\t{self.name}\t({self.year})\t(imdb: {self.imdbid})"


class ExtTvSeries(info.TvSeries):
    def __init__(self, tv_series):
        super().__init__(
            tv_series.name,
            tv_series.year,
            tv_series.imdbid,
            tv_series.get_dirname(),
            tv_series.get_filename(),
        )

    def __str__(self):
        return f"(TV Series)\t{self.name}\t({self.year})\t(imdb: {self.imdbid})"


# Helper function to make it easier to build the appropriate extended `Media`
def build_extended_media(obj):
    CLASS_MAP = {
        info.Movie: ExtMovie,
        info.TvSeries: ExtTvSeries,
    }

    # Use the correct extended class for `obj`
    class_type = CLASS_MAP[type(obj)]
    return class_type(obj)


class ExtSearchResult(info.SearchResult):
    def __init__(self, search_result):
        # All of the members are named the same the params so we can just pass in
        super().__init__(**search_result.__dict__)

    def __str__(self):
        TIME_FMT = "%Y-%m-%d %H:%M:%S"
        upload = dt.strftime(self.upload_date, TIME_FMT)
        sub = self.subtitles
        author = "NA" if self.author is None else self.author.name
        return f"[{upload} | by {author} | {sub.ext}] {sub.filename}"


class OutOfBoundsError(Exception):
    pass


class BadResponseError(Exception):
    pass


if __name__ == "__main__":
    main()
