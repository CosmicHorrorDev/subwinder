# Custom Classes

This consists of the classes defined in the `subwinder.info`, `subwinder.media`, and `subwinder.results` modules.

---

## Table of Contents

* [`subwinder.info` module](#subwinderinfo-module)
    * [`build_media_info()`](#build_media_infodata-dirname-filename)
    * [`UserInfo`](#userinfo)
    * [`FullUserInfo`](#fulluserinfo-derived-from-userinfo)
    * [`Comment`](#comment)
    * [`MediaInfo`](#mediainfo)
    * [`MovieInfo`](#movieinfo-derived-from-mediainfo)
    * [`TvSeriesInfo`](#tvseriesinfo-derived-from-mediainfo)
    * [`EpisodeInfo`](#episodeinfo-derived-from-tvseriesinfo)
        * [`EpisodeInfo.from_tv_series()`](#episodeinfofrom_tv_seriestv_series-season-episode)
    * [`DownloadInfo`](#downloadinfo)
    * [`ServerInfo`](#serverinfo)
    * [`SubtitlesInfo`](#subtitlesinfo)
* [`subwinder.media` module](#subwindermedia-module)
    * [`Subtitles`](#subtitles)
    * [`Media`](#media)
        * [Initialization](#initialization)
        * [`Media.from_file()`](#mediafrom_filefilepath)
        * [`.set_filepath()`](#set_filepathfilepath)
        * [`.set_filename()`](#set_filenamefilename)
        * [`.set_dirname()`](#set_dirnamedirname)
* [`subwinder.results` module](#subwinderresults-module)
    * [`SearchResult`](#searchresult)

---

## `subwinder.info` module

This module contains a number of info classes used by the API as well as a helper function to handle building the correct `MediaInfo` derivative automatically.

```python
from subwinder.info import (
    build_media_info,
    UserInfo,
    FullUserInfo,
    Comment,
    MediaInfo,
    MovieInfo,
    TvSeriesInfo,
    EpisodeInfo,
    SubtitlesInfo,
)
```

### `build_media_info(data, dirname, filename)`

This function is used to automatically create the correct `MediaInfo` object from `data`. This of course requires the information for the correct `MediaInfo` to be built.

```python
movie = build_media_info(
    {
        "IDMovieIMDB": "0090605",
        "MovieName": "Aliens",
        "MovieYear": "1986",
        "MovieKind": "movie",
    }
)
assert type(movie) == MovieInfo

tv_series = build_media_info(
    {
        "IDMovieIMDB": "0813715",
        "MovieName": "Heros",
        "MovieYear": "2006",
        "MovieKind": "tv series",
    }
)
assert type(tv_series) == TvSeriesInfo
```

### `UserInfo`

`dataclass` containing the bare amount of information for a user.

| Member | Type | Description |
| :---: | :---: | :--- |
| `id` | `str` | The user's unique id provided by opensubtitles |
| `name` | `str` | The name of the user |

### `FullUserInfo` derived from `UserInfo`

Contains more thorough information on a user.

| Member | Type | Description |
| :---: | :---: | :--- |
| `num_downloads` | `int` | The total number of subtitles downloaded by the user |
| `num_uploads` | `int` | The total number of subtitles uploaded by the user |
| `preferred_langauges` | `list<str>` | List of the preferred languages in the 2 letter format |
| `rank` | `str` | The opensubtitles rank of the user |
| `web_languages` | `str` | The 2 letter language code used for the user on the website |

### `Comment`

This stores all the information to represent a comment.

| Member | Type | Description |
| :---: | :---: | :--- |
| `author` | `UserInfo` | The author of the comment |
| `text` | `str` | The comment's text |
| `date` | `datetime.datetime` | When the comment was left |

### `MediaInfo`

This is the base class used for representing several kinds of media returned by the API.

| Member | Type | Description |
| :---: | :---: | :--- |
| `dirname` | `pathlib.Path` | The optional directory of the original media searched for |
| `filename` | `pathlib.Path` | The optional filename of the original media file searched for |
| `imdbid` | `str` | The imdbid for the media |
| `name` | `str` | The name of the media |
| `year` | `int` | The year the media was released |

### `MovieInfo` derived from `MediaInfo`

This class represents a movie returned by the API. The members are identical to `MediaInfo` with the extra context that it's specifically for a movie.

_Members are identical to `MediaInfo`_

### `TvSeriesInfo` derived from `MediaInfo`

Much like `MovieInfo` this class represents a TV series returned by the API. The members are again identical to `MediaInfo` with the extra context that it's specifically for a TV series.

_Members are identical to `MediaInfo`_

### `EpisodeInfo` derived from `TvSeriesInfo`

An episode belonging to a tv series, much like `TvSeriesInfo`, but with a season and episode number.

| Member | Type | Description |
| :---: | :---: | :--- |
| - | - | All members from `MediaInfo` |
| `episode` | `int` | The episode number for this episode |
| `season` | `int` | The season number for this episode |

#### `EpisodeInfo.from_tv_series(tv_series, season, episode)`

This `classmethod` provides the ability to create an `EpisodeInfo` from an existing `TvSeriesInfo`. This can be used when the API returns a `TvSeriesInfo` and you would like to use a method that requires a `EpisodeInfo` instead such as `AuthSubwinder`'s `search_subtitles` method. This information could be entered manually or found using something like a regex on the filename.

| Param | Type | Description |
| :---: | :---: | :--- |
| `tv_series` | `TvSeriesInfo` | The TV Series that this episode belongs to |
| `season` | `int` | The season number for this episode |
| `episode` | `int` | The episode number for this episode |

```python
# Let's assume we know we want to search for subtitles for the S01E02 of
# `tv_series`
episode = EpisodeInfo.from_tv_series(tv_series, 1, 2)
```

### `DownloadInfo`

This class contains various information on the daily download info for the current user.

| Member | Type | Description |
| :---: | :---: | :--- |
| `downloaded` | `int` | The number of subtitles downloaded today |
| `ip` | `str` | The IP address used to keep track of the user |
| `limit` | `int` | The daily download limit for the user |
| `limit_checked_by` | `str` | How the limit is tracked (normally by `"user_ip"`) |
| `remaining` | `int` | The remaining number of daily downloads for the user|

### `ServerInfo`

This class represents various information about the opensubtitles server.

| Member | Type | Description |
| :---: | :---: | :--- |
| `application` | `str` | The current application program name |
| `bots_online` | `int` | The number of bots currently online |
| `daily_download_info` | `DownloadInfo` | Information about the user's daily downloads |
| `total_subtitles_downloaded` | `int` | The total number of subtitle files downloaded |
| `total_subtitle_files` | `int` | The number of subtitle files available |
| `total_movies` | `int` | The number of movies tracked |
| `users_logged_in` | `int` | The number of users that are logged in |
| `users_online` | `int` | The number of users currently online |
| `users_online_peak` | `int` | The peak number of users ever online |
| `users_registered` | `int` | The number of users with accounts |

### `SubtitlesInfo`

This class covers various information about a subtitle file.

| Member | Type | Description |
| :---: | :---: | :--- |
| `encoding` | `str` | The text encoding type of the subtitles file |
| `ext` | `str` | The extension of the subtitles file |
| `file_id` | `str` | The unique id for the subtitles file (not sure why this is separate from `id` |
| `filename` | `pathlib.Path` | The uploaded filename given for the subtitles |
| `id` | `str` | The unique id for the subtitles |
| `lang_2` | `str` | The subtitles' language in the 2 letter format |
| `lang_3` | `str` | The subtitles' language in the 3 letter format |
| `num_comments` | `int` | The number of comments left on the subtitles |
| `num_downloads` | `int` | The number of times these subtitles were downloaded |
| `rating` | `float` or `None` | If no ratings are left then `rating` is `None` otherwise its the average rating left on the subtitles |
| `size` | `int` | The size of the subtitles file in bytes |
| `sub_to_movie_id` | `str` or `None` | The unique id tying these subtitles to a movie hash. Will be `None` if this search wasn't matched using a `Media` object |

---

## `subwinder.media` module

This module just contains the `Subtitles` and `Media` classes used to create objects from local files.

```python
from subwinder.media import Media, Subtitles
```

### `Subtitles`

This class honestly seems useless at his point, if I get anything about it figured out then I'll update this.

### `Media`

This class is used to get the `special_hash` and filesize of a media file which is useful for searching for subtitles using an exact file match.

| Member | Type | Description |
| :---: | :---: | :--- |
| `dirname` | `pathlib.Path` or `None` | (Default `None`) Optional directory of the local media file |
| `filename` | `pathlib.Path` or `None` | (Default `None`) Optional file name of the local media file |
| `hash` | `str` | The hexadecimal `special_hash` of the media |
| `size` | `int` | The size of the media in bytes |

#### Initialization

_Note: `hash` and `size` are just stored directly_

| Param | Type | Description |
| :---: | :---: | :--- |
| `filepath` | `pathlib.Path` or `None` | (Default `None`) Optional path to the local media file |
| `hash` | `str` | _Refer to member_ |
| `size` | `int` | _Refer to member_ |

#### `Media.from_file(filepath)`

This `classmethod` makes it easy to build a `Media` object directly from a local file using the file's `filepath`.


| Param | Type | Description |
| :---: | :---: | :--- |
| `filepath` | `str` or `pathlib.Path` | Path to the local media file |

**Returns:** `Media` object representing the media at `filepath`

```python
from pathlib import Path

movie = Media.from_file("/path/to/movie.mp4")
episode = Media.from_file(Path("/path/to/episode.avi"))
```

#### `.set_filepath(filepath)`

Sets the `filename` and `dirname` for the `Media`. Useful for when you can't initialize the `Media` using `.from_file(filepath)`, but you want to have subtitles downloaded using the directory and filename from `filepath`.

| Param | Type | Description |
| :---: | :---: | :--- |
| `filepath` | `str` or `pathlib.Path` | Path to associate this `Media` with |

**Returns:** `None`

```python
from pathlib import Path

# Assuming we have a `Media` with no `filename` and `dirname` info
assert media.filename is None and media.dirname is None

media.set_filepath("/path/to/movie.mkv")

# Both `dirname` and `filename` are set now
assert media.dirname == Path("/path/to")
assert media.filename == Path("movie.mkv")
```

#### `.set_filename(filename)`

Sets the `filename` for the `Media`. Like `.set_filepath(filepath)` this is useful when you can't initialize the `Media` with `.from_file(filepath)`, but you want the context of the `filename` when downloading the subtitles.

| Param | Type | Description |
| :---: | :---: | :--- |
| `filename` | `str` or `pathlib.Path` | Filename to associate this `Media` with |

**Returns:** `None`

```python
from pathlib import Path

# Assume there is currently no `filename` for `media`
assert media.filename is None

media.set_filename("episode.mp4")
# Now `filename` is the `Path` for the given `filename`
assert media.filename == Path("episode.mp4")
```

### `.set_dirname(dirname)`

Sets the `dirname` for the `Media`. Like `.set_filepath(filepath)` this is useful when you can't initialize the `Media` with `.from_file(filepath)`, but you want to automatically save the subtitles for this `Media` in `dirname`.

| Param | Type | Description |
| :---: | :---: | :--- |
| `dirname` | `str` or `pathlib.Path` | Directory to associate this `Media` with |

**Returns:** `None`

```python
from pathlib import Path

# Assume there is currenly no `dirname` for `media`
assert media.dirname is None

media.set_dirname("/some/given/path")
# Now `dirname` is the `Path` for the given directory
assert media.dirname == Path("/some/given/path")
```

---

## `subwinder.results` module

This module just contains the `SearchResult` class and should likely just be merged into `subwinder.info`

```python
from subwinder.results import SearchResult
```

### `SearchResult`

This class represents a result returned by `AuthSubwinder`'s `search_subtitles` method.

| Member | Type | Description |
| :---: | :---: | :--- |
| `author` | `UserInfo` or `None` | Optional author who uploaded the subtitles |
| `media` | `MovieInfo` or `EpisodeInfo` | The media these subtitles are for |
| `subtitles` | `SubtitlesInfo` | The object representing information about these subtitles |
| `upload_date` | `datetime.datetime` | The date the subtitles were uploaded |
