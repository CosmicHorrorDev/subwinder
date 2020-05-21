#!/usr/bin/env python
from subwinder import info, AuthSubwinder, Media
from subwinder.exceptions import SubHashError

from itertools import repeat
import re


def main():
    LANG = "en"
    # Match on a s<num>e<num> snippet for `TvSeriesInfo`
    EPISODE_REGEX = re.compile(r"s(\d{1,})e(\d{1,})", re.IGNORECASE)
    # So let's start off assuming we have two files like in the original Quickstart
    MEDIA_FILEPATHS = ["/path/to/movie.mkv", "/path/to/episode.avi"]

    # First thing is to get `Media` objects for the files we want subtitles for
    media = []
    for filepath in MEDIA_FILEPATHS:
        # Hashing fails if the file is too small (under 128 KiB)
        try:
            media.append(Media(filepath))
        except SubHashError:
            pass

    # And now we'll start searching (assumes credentials are set with env vars)
    with AuthSubwinder() as asw:
        # (to simplify things I'm just doing one lang)
        # TODO: it would be nice to be able to pass in `zip` and have it expand
        #       internally just to make it a little nicer. Sadly there's no iterable
        #       class that I can check for so guess I can add `zip` to the list
        results = asw.search_subtitles(list(zip(media, repeat(LANG))))
        # And now we'll assume that _at least one_ result didn't find an exact match
        # (peeking under the hood, the search above occurs with the file hash and size
        # to get an exact match which fails when no subtitles are linked to that exact
        # file, falling back could happen internally, but yields worse results so I
        # want the action to be explicit instead)
        assert None in results

        # Now let's fallback to getting a `MediaInfo` match from the filenames (this
        # endpoint isn't supposed to be spammed so please only use it as a fall back)
        unmatched = [m for m, result in zip(media, results) if result is None]
        unmatched_names = [media.filename for media in unmatched]
        guesses = asw.guess_media(unmatched_names)

        # Filter out any `None` since there isn't much else to fall back to
        unmatched = [m for m, guess in zip(unmatched, guesses) if guess is not None]
        guesses = [guess for guess in guesses if guess is not None]

        # We need to iterate over the content backwards because we may remove entries
        # while iterating over them
        for rev_i in range(len(guesses) - 1, -1, -1):
            # `.guess_media(...)` loses file location context so let's get that back
            # TODO: would be nice to include a `.get_filepath()` too
            guesses[rev_i].set_filename(unmatched[rev_i].filename)
            guesses[rev_i].set_dirname(unmatched[rev_i].dirname)

            # So now we run into a pretty minor issue. We want to search using these
            # guesses that we have now, and the guesses are either `MovieInfo` or
            # `TvSeriesInfo`
            # - `MovieInfo` can be searched directly now, nothing extra to do
            # - `TvSeriesInfo` is a bit more complicated. We need to somehow get the
            #    series and episode number for the specific episode to make it into an
            #    `EpisodeInfo`. In this example I'm just gonna use a regex, but for your
            #    case you may have more context on what you're searching for already
            if isinstance(guesses[rev_i], info.TvSeriesInfo):
                matches = EPISODE_REGEX.search(guesses[rev_i].filename)
                if matches is None:
                    # Remove this entry since the regex failed
                    guesses.pop(rev_i)
                else:
                    season_num = int(matches.group(1))
                    episode_num = int(matches.group(2))

                    # Replace the `TvSeriesInfo` with the correct `EpisodeInfo`
                    guesses[rev_i] = info.EpisodeInfo.from_tv_series(
                        guesses[rev_i], season_num, episode_num
                    )

        # Now we can search for all the missing media that we have guesses for
        new_results = asw.search_subtitles(list(zip(guesses, repeat(LANG))))

    # And now here is our final list of results that we can use, if you wanted you could
    # do a little more to keep track of the `Media` these are associated with, but
    # each result should still have the `filename` and `dirname` associated with it
    results += new_results
    results = [result for result in new_results if result is not None]  # :tada:


if __name__ == "__main__":
    main()
