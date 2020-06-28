# Custom Classes

This consists of the classes defined in the [`subwinder.info`](#subwinderinfo-module) module and the [`Media`](#media) object from the base `subwinder` module.

---

## Table of Contents

* [`subwinder.info` module](#subwinderinfo-module)
    * [`build_media_info()`](#build_media_infodata)
    * [`UserInfo`](#userinfo)
    * [`FullUserInfo`](#fulluserinfo-derived-from-userinfo)
    * [`Comment`](#comment)
    * [`GuessMediaResult`](#guessmediaresult)
    * [`MediaInfo`](#mediainfo)
        * [Getters and Setters](#getters-and-setters)
    * [`MovieInfo`](#movieinfo-derived-from-mediainfo)
    * [`TvSeriesInfo`](#tvseriesinfo-derived-from-mediainfo)
    * [`EpisodeInfo`](#episodeinfo-derived-from-tvseriesinfo)
        * [`EpisodeInfo.from_tv_series()`](#episodeinfofrom_tv_seriestv_series-season-episode)
    * [`DownloadInfo`](#downloadinfo)
    * [`SearchResult`](#searchresult)
    * [`ServerInfo`](#serverinfo)
    * [`SubtitlesInfo`](#subtitlesinfo)
* [`Media`](#media)
    * [Initialization](#initialization)
    * [`Media.from_parts()`](#mediafrom_partshash-size-dirname-filename)
    * [Getters and Setters](#getters-and-setters-1)

---

## `subwinder.info` module

This module contains a number of info classes used by the API as well as a helper function to handle building the correct [`MediaInfo`](#mediainfo) derivative automatically.

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
    DownloadInfo,
    SearchResult,
    ServerInfo,
    SubtitlesInfo,
)
```

### `build_media_info(data)`

This function is used to automatically create the correct [`MediaInfo`](#mediainfo) object from `data`. This of course requires the information for the correct [`MediaInfo`](#mediainfo) to be built.

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
| `author` | [`UserInfo`](#userinfo) | The author of the comment |
| `text` | `str` | The comment's text |
| `date` | `datetime.datetime` | When the comment was left |

### `GuessMediaResult`

This stores all the information returned when guessing media (used by `guess_media`'s ranking function and returned directly by the unranked variant).

| Member | Type | Description |
| :---: | :---: | :--- |
| `best_guess` | [`MovieInfo`](#movieinfo), [`EpisodeInfo`](#episodeinfo), or `None` | The best guess for the provided query |
| `from_string` | [`MovieInfo`](#movieinfo), [`EpisodeInfo`](#episodeinfo), or `None` | The guess purely from the provided string |
| `from_imdb` | `List[MovieInfo, EpisodeInfo, or None]` [[0]](#movieinfo) [[1]](#episodeinfo) | List of results based off IMDB (I'm really just guessing at this point) |

### `MediaInfo`

This is the base class used for representing several kinds of media returned by the API.

| Member | Type | Description |
| :---: | :---: | :--- |
| `_dirname` | `pathlib.Path` | The optional directory of the original media searched for |
| `_filename` | `pathlib.Path` | The optional filename of the original media file searched for |
| `imdbid` | `str` | The imdbid for the media |
| `name` | `str` | The name of the media |
| `year` | `int` | The year the media was released |

#### Getters and Setters

All the getters and setters should be pretty self explanatory. These all deal with `_dirname` and `_filename`.

| Method | Input | Output | Desc. |
| :---: | :---: | :---: | :--- |
| `.get_filename()` `.set_filename(filename)` | path-like value or `None` | `pathlib.Path` or `None` | Set\Get `_filename` |
| `.get_dirname()` `.set_dirname(dirname)` | path-like value or `None` | `pathlib.Path` or `None` | Set\Get `_dirname` |
| `.get_filepath()` `.set_filepath(filepath)` | path-like value or `None` | `pathlib.Path` or `None` | Set\Get path given by `_dirname` and `_filename` |

```python
from pathlib import Path

# Assuming we have a `MediaInfo` with no `_filename` and `_dirname` info
assert media_info.get_filename() is None and media_info.get_dirname() is None

# Equivalent to `media.set_filepath("/path/to/movie.mkv")`
media_info.set_filename("movie.mkv")
media_info.set_dirname("/path/to")

# Both `_dirname` and `_filename` are set now
assert media_info.get_dirname() == Path("/path/to")
assert media_info.get_filename() == Path("movie.mkv")
# We can also get the full path back
assert media_info.get_filepath() == Path("/path/to/movie.mkv")
```

#### `.get_filepath()`

Gets the path represented by `_dirname` and `_filename` or `None` if neither are set.

**Returns:** `pathlib.Path` or `None`

#### `.set_filepath(filepath)`

Sets the `_filename` and `_dirname` for the `MediaInfo`. Useful for when you can't initialize the `MediaInfo` using the normal constructor, but you want to have subtitles downloaded using the directory and filename from `filepath`.

| Param | Type | Description |
| :---: | :---: | :--- |
| `filepath` | `str` or `pathlib.Path` | Path to associate this `MediaInfo` with |

**Returns:** `None`

```python
from pathlib import Path

# Assuming we have a `MediaInfo` with no `_filename` and `_dirname` info
assert media_info.get_filepath() is None

media_info.set_filepath("/path/to/movie.mkv")

# Both `_dirname` and `_filename` are set now
assert media_info.get_dirname() == Path("/path/to")
assert media_info.get_filename() == Path("movie.mkv")
# We can also get the full file path too
assert media_info.get_filepath() == Path("/path/to/movie.mkv")
```

#### `.get_filename()`

Gets `_filename`.

**Returns:** `pathlib.Path` or `None`

#### `.set_filename(filename)`

Sets the `_filename` for the `MediaInfo`. Like `.set_filepath(filepath)` this is useful when you can't initialize the `MediaInfo` using the normal constructor, but you want the context of the `_filename` when downloading the subtitles.

| Param | Type | Description |
| :---: | :---: | :--- |
| `filename` | `str` or `pathlib.Path` | Filename to associate this `MediaInfo` with |

**Returns:** `None`

```python
from pathlib import Path

# Assume there is currently no `_filename` for `media_info`
assert media_info.get_filename() is None

media_info.set_filename("episode.mp4")
# Now `_filename` is the `Path` for the given filename
assert media_info.get_filename() == Path("episode.mp4")
```

#### `.get_dirname()`

Gets `_dirname`.

**Returns:** `pathlib.Path` or `None`

### `.set_dirname(dirname)`

Sets the `_dirname` for the `MediaInfo`. Like `.set_filepath(filepath)` this is useful when you can't initialize the `MediaInfo` using the normal constructor, but you want to automatically save the subtitles for this `MediaInfo` in `_dirname`.

| Param | Type | Description |
| :---: | :---: | :--- |
| `dirname` | `str` or `pathlib.Path` | Directory to associate this `MediaInfo` with |

**Returns:** `None`

```python
from pathlib import Path

# Assume there is currenly no `_dirname` for `media_info`
assert media_info.get_dirname() is None

media_info.set_dirname("/some/given/path")
# Now `_dirname` is the `Path` for the given directory
assert media_info.get_dirname() == Path("/some/given/path")
```

### `MovieInfo` derived from `MediaInfo`

This class represents a movie returned by the API. The members are identical to [`MediaInfo`](#mediainfo) with the extra context that it's specifically for a movie.

_Members are identical to [`MediaInfo`](#mediainfo)_

### `TvSeriesInfo` derived from `MediaInfo`

Much like [`MovieInfo`](#movieinfo-derived-from-mediainfo) this class represents a TV series returned by the API. The members are again identical to [`MediaInfo`](#mediainfo) with the extra context that it's specifically for a TV series.

_Members are identical to [`MediaInfo`](#mediainfo)_

### `EpisodeInfo` derived from `TvSeriesInfo`

An episode belonging to a tv series, much like [`TvSeriesInfo`](#tvseriesinfo-derived-from-mediainfo), but with a season and episode number.

| Member | Type | Description |
| :---: | :---: | :--- |
| - | - | All members from [`MediaInfo`](#mediainfo) |
| `episode` | `int` | The episode number for this episode |
| `season` | `int` | The season number for this episode |

#### `EpisodeInfo.from_tv_series(tv_series, season, episode)`

This `classmethod` provides the ability to create an `EpisodeInfo` from an existing [`TvSeriesInfo`](#tvseriesinfo-derived-from-mediainfo). This can be used when the API returns a [`TvSeriesInfo`](#tvseriesinfo-derived-from-mediainfo) and you would like to use a method that requires a `EpisodeInfo` instead such as [`AuthSubwinder`'s `search_subtitles` method](Authenticated-Endpoints.md#search_subtitlesqueries-ranking_func-rank_args-rank_kwargs). This information could be entered manually or found using something like a regex on the filename.

| Param | Type | Description |
| :---: | :---: | :--- |
| `tv_series` | [`TvSeriesInfo`](#tvseriesinfo-derived-from-mediainfo) | The TV Series that this episode belongs to |
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

### `SearchResult`

This class represents a result returned by [`AuthSubwinder`'s `search_subtitles`](Authenticated-Endpoints.md#search_subtitlesqueries-ranking_func-rank_args-rank_kwargs) method.

| Member | Type | Description |
| :---: | :---: | :--- |
| `author` | [`UserInfo`](#userinfo) or `None` | Author who uploaded the subtitles. `None` indicates the subtitles were uploaded anonymously. |
| `media` | [`MovieInfo`](#movieinfo-derived-from-mediainfo) or [`EpisodeInfo`](#episodeinfo-derived-from-tvseriesinfo) | The media these subtitles are for |
| `num_bad_reports` | `int` | I'm guessing this is the number of times this result has been commented on as "bad". The documentation states that it's "self-explained" :upside_down_face: |
| `num_comments` | `int` | The number of comments left on this result |
| `num_downloads` | `int` | The number of times these subtitles were downloaded |
| `score` | `float` | How well the API judged this as a match for the provided query (I'm guessing higher is better, I don't think this value is even mentioned in the API :upside_down_face:) |
| `subtitles` | [`SubtitlesInfo`](#subtitlesinfo) | The object representing information about these subtitles |
| `rating` | `float` or `None` | If no ratings are left then `rating` is `None` otherwise its the average rating left on the subtitles |
| `upload_date` | `datetime.datetime` | The date the subtitles were uploaded |

### `ServerInfo`

This class represents various information about the opensubtitles server.

| Member | Type | Description |
| :---: | :---: | :--- |
| `application` | `str` | The current application program name |
| `bots_online` | `int` | The number of bots currently online |
| `daily_download_info` | [`DownloadInfo`](#downloadinfo) | Information about the user's daily downloads |
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
| `size` | `int` | The size of the subtitles file in bytes |
| `sub_to_movie_id` | `str` or `None` | The unique id tying these subtitles to a movie hash. Will be `None` if this search wasn't matched using a [`Media`](#media) object |

---

### `Media`

This class is used to get the `special_hash` and filesize of a media file which is useful for searching for subtitles using an exact file match.

| Member | Type | Description |
| :---: | :---: | :--- |
| `_dirname` | `pathlib.Path` or `None` | (Default `None`) Optional directory of the local media file |
| `_filename` | `pathlib.Path` or `None` | (Default `None`) Optional file name of the local media file |
| `hash` | `str` | The hexadecimal `special_hash` of the media |
| `size` | `int` | The size of the media in bytes |

```python
from subwinder import Media
```

#### Initialization

Builds a `Media` object directly from a local file using the file's `filepath`.


| Param | Type | Description |
| :---: | :---: | :--- |
| `filepath` | `str` or `pathlib.Path` | Path to the local media file |

**Returns:** `Media` object representing the media at `filepath`

```python
from pathlib import Path

movie = Media("/path/to/movie.mp4")
episode = Media(Path("/path/to/episode.avi"))
```

#### `Media.from_parts(hash, size, dirname, filename)`

_Note: If possible it is preferred to build the media from the [constructor](#initialization)_

_Note: `hash` and `size` are just stored directly while dirname and filename will be converted to `Path`s_

_All parameters match the members in the order `Media(hash, size, dirname=None, filename=None)`_

```python
# Build a movie to search from using the hash and filesize
# Note: this will not have context for the original filename or what
# directory to download into like it would if you used the normal constructor
movie = Media.from_parts("<movie-hash>", <movie-filesize>)
```

#### Getters and Setters

All the getters and setters should be pretty self explanatory. These all deal with `_dirname` and `_filename`.

| Method | Input | Output | Desc. |
| :---: | :---: | :---: | :--- |
| `.get_filename()` `.set_filename(filename)` | path-like value or `None` | `pathlib.Path` or `None` | Set\Get `_filename` |
| `.get_dirname()` `.set_dirname(dirname)` | path-like value or `None` | `pathlib.Path` or `None` | Set\Get `_dirname` |
| `.get_filepath()` `.set_filepath(filepath)` | path-like value or `None` | `pathlib.Path` or `None` | Set\Get path given by `_dirname` and `_filename` |

```python
from pathlib import Path

# Assuming we have a `Media` with no `_filename` and `_dirname` info
assert media.get_filename() is None and media.get_dirname() is None

# Equivalent to `media.set_filepath("/path/to/movie.mkv")`
media.set_filename("movie.mkv")
media.set_dirname("/path/to")

# Both `_dirname` and `_filename` are set now
assert media.get_dirname() == Path("/path/to")
assert media.get_filename() == Path("movie.mkv")
# We can also get the full path back
assert media.get_filepath() == Path("/path/to/movie.mkv")
```
