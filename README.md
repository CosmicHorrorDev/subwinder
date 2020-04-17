## Subwinder

An ergonomic python library for the [opensubtitles.org](https://opensubtitles.org) API.

### Quickstart

Our task is composed of 3 simple steps

1. Search for English subtitles for a movie at `/path/to/movie.mkv` and French subtitles for a tv show episode at `/path/to/episode.avi`.
2. Print out any comments that people left on the subtitles.
3. Download the subtitles next to the original media file with the naming format `{media name}.{3 letter lang code}.{extension}` (something like `/path/to/movie.eng.ssa` and `/path/to/episode.fre.srt`)

**Note:** This does require a free opensubtitles account.

**Note:** The user agent is specific to the program using the API. You can look [here](https://trac.opensubtitles.org/projects/opensubtitles/wiki/DevReadFirst) under "How to request a new user agent" to see about what user agent you can set for development, or how to get an official user agent for your program.

```python
from subwinder.auth import AuthSubwinder
from subwinder.media import Media

from datetime import datetime as dt

# Step 1. Getting our `Media` objects created and searching
movie = Media.from_file("/path/to/movie.mkv")
episode = Media.from_file("/path/to/episode.avi")
with AuthSubwinder("<username>", "<password>", "<useragent>") as asw:
    results = asw.search_subtitles([(movie, "en"), (episode, "fr")])
    # We're assuming both `Media` returned a `SearchResult` for this example
    assert None not in results

    # Step 2. Print any comments for both of our `SearchResult`s
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    results_comments = asw.get_comments(results)
    for result, result_comments in zip(results, results_comments):
        print(f"{result.media.filename} Comments:")
        for comment in result_comments:
            date = dt.strftime(comment.date, TIME_FORMAT)
            print(f"{date} {comment.author.name}: {comment.text}")
        print()

    # Step 3. Download both of the subtitles next to the original files
    # We're assuming we have enough remaining downloads for these, if not then
    # a `SubDownloadError` will be raised by `.download_subtitles(...)`
    assert asw.daily_download_info().remaining >= len(results)
    download_paths = asw.download_subtitles(
        results, name_format="{media_name}.{lang_3}.{ext}"
    )
```

And that's it, with ~20 sloc you can search, get comments, and download a couple subtitles!

### Installation

**Note:** The minimum required Python version is `3.7`, you can check your current version with `python -V` or `python3 -V` if you're unsure of your current version.

Install the subwinder library with your standard Python package manager e.g.

```text
$ pip install subwinder
```

As always you are recommended to install into a virtual environment.

### Documentation

There is pretty thorough documentation in the [repo's wiki](https://github.com/LovecraftianHorror/subwinder/wiki) that covers all the functionality currently exposed by the library. If anything in the wiki is incorrect or confusing then please [raise an issue](https://github.com/LovecraftianHorror/subwinder/issues) to address this.

### Benefits from using `subwinder`

* Easy to develop in
    * Use objects defined by the library, and take and return objects in a logical order to provide a clean interface
    * Efforts are made to prevent re-exposing the same information under slightly different key names, or under different types to provide a consistent experience
    * Values are parsed to built-in Python types when it makes sense
    * Endpoints that batch do so automatically to the maximum batch size
* Robust, but if it fails then fail fast
    * Custom `Exception`s are defined and used to provide context on failures
    * If something will fail, try to detect it and raise an `Exception` as early as possible
    * Automatically retry requests using an exponential back-off to deal with rate-limiting
* Small footprint
    * No external dependencies are required

### Caveats from using `subwinder`

* Python 3.7+ is required (at this point 3.7 is already several years old)
* Not all values from the API are exposed: however, I'm flexible on this so if you have a use for one of the missing values then please bring it up in [an issue](https://github.com/LovecraftianHorror/subwinder/issues)!
* Currently only English is supported for the internal API. You can still search for subtitles in other languages, but the media names and long language names will all be in English. This will be worked on after the API is in a more stable state

### License

`subwinder` is licensed under AGPL v3 which should be included with the library. If not then you can find an online copy [here](https://www.gnu.org/licenses/agpl-3.0.en.html).
