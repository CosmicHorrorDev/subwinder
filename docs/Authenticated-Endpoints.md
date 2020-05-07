# Authenticated Endpoints

All functionality with the authenticated API is exposed from `subwinder` through the [`AuthSubwinder`](#authsubwinder) class.

---

## Table of Contents

* [`AuthSubwinder`](#authsubwinder)
    * [Initialization](#initialization)
    * [`.add_comment()`](#add_commentsearch_result-comment_str-bad)
    * [`.auto_update()`](#auto_updateprogram_name)
    * [`.download_subtitles()`](#download_subtitlesdownloads-download_dir-name_format)
    * [`.get_comments()`](#get_commentssearch_results)
    * [`.guess_media()`](#guess_mediaqueries-ranking_func-rank_args-rank_kwargs)
    * [`.preview_subtitles`](#preview_subtitlesqueries)
    * [`.ping()`](#ping)
    * [`.report_movie()`](#report_moviesearch_result)
    * [`.search_subtitles()`](#search_subtitlesqueries-ranking_func-rank_args-rank_kwargs)
    * [`.suggest_media()`](#suggest_mediaquery)
    * [`.user_info()`](#user_info)
    * [`.vote()`](#votesearch_result-score)

---

## `AuthSubwinder`

The class that handles all authenticated functionality exposed by the opensubtitles API.

```python
from subwinder import AuthSubwinder
```

### Initialization

`AuthSubwinder` is initialized using a `with` statement to handle automatically logging in and out of the API.

| Param | Type | Description |
| :---: | :---: | :--- |
| `username` | `str` or `None` | (Default `None`) opensubtitles account username, can also be set with the `OPEN_SUBTITLES_USERNAME` env var |
| `password` | `str` or `None` | (Default `None`) opensubtitles account password, can also also be set with the `OPEN_SUBTITLES_PASSWORD` env var |
| `useragent` | `str` or `None` | (Default `None`) [Program's useragent](https://trac.opensubtitles.org/projects/opensubtitles/wiki/DevReadFirst), can also be set with the `OPEN_SUBTITLES_USERAGENT` env var |

**Returns:** `AuthSubWinder` object representing actions for the user matching the supplied credentials

```python
with AuthSubwinder("<username>", "<password>", "<useragent>") as asw:
    ...
```

### `.add_comment(search_result, comment_str, bad)`

Adds a comment to the `search_result` were the text is `comment_str` and optionally you may indicate whether the comment is to indicate that the subtitles for the `search_result` are `bad`.

| Param | Type | Description |
| :---: | :---: | :--- |
| `search_result` | [`SearchResult`](CustomClasses.md#searchresult) | Search result to leave the comment on |
| `comment_str` | `str` | The text for the comment |
| `bad` | `bool` | (Default `False`) Indicate whether the comment is because the subtitles are bad |

```python
# Leave a comment for subtitles you liked
asw.add_comment(search_result1, "Perfect subtitles!")

# Leave a comment on some bad subtitles (Ex: would be if the subtitles aren't
# in sync even if the match was using the size and hash)
asw.add_comment(
    search_result2,
    "Subtitles weren't synced even though the match was with hash and size",
    bad=True,
)
```

### `.auto_update(program_name)`

Useful for programs using this library, returns current information for `program_name` allowing for programs to know when an update is required.

| Param | Type | Description |
| :---: | :---: | :--- |
| `program_name` | `str` | The name of the current program |

**Returns:** `dict` containing information about the program. See example below for more information

```python
info = asw.auto_update("SubDownloader")

print(info)
# Info will have some information like
# {
#     "version": "{program_version_number}",
#     "url_windows": "{url_for_windows_download}",
#     "url_linux": "{url_for_linux_download}",
#     "comments": "{comment_for_latest_release}"
# }
```

### `.download_subtitles(downloads, download_dir, name_format)`

Download subtitles will download the subtitles for all the `downloads` either beside the original media or to `download_dir` using the naming scheme specified by `name_format`. The API limits requests to 20 downloads, but this library automatically batches the requests in groups of 20 for you. However there is also a daily limit on downloads, so if the number of downloads will put the user over that limit then this will raise a [`SubDownloadError`](Exceptions.md#subdownloaderror). You can check the number of remaining downloads and chunk the request with `.daily_download_info().remaining` to prevent this.


| Param | Type | Description |
| :---: | :---: | :--- |
| `downloads`| [`List[SearchResult]`](Custom-Classes.md#searchresult) | Search results to download subtitles for |
| `download_dir` | `str`, `pathlib.Path`, or `None` | (Default `None`) The directory the subtitles are downloaded into. If `None` it will attempt to download next to the original [`Media`](Custom-Classes.md#media) file: however, some [`SearchResult`s](Custom-Classes.md#searchresult) will not be associated to a media (`.media.dirname is None`) so this will raise a [`SubDownloadError`](Exceptions.md#subdownloaderror). This can be fixed by either setting `download_dir` or by setting any missing `.media.dirname` |
| `name_format` | `str` | (Default `"{upload_filename}"`) is the format used to name the downloaded subtitles. It defaults to the uploaded filename for the subtitles: however, it gets `format`ed with possible values including `media_name` for the name of the [`Media`](Custom-Classes.md#media) without the file extension that was searched for (same situation as `download_dir`, may have to set `.media.filename`), `lang_2`, `lang_2`, `ext` for the extension, `upload_name`, `upload_filename`. A popular format would be `"{media_name}.{lang_3}.{ext}"` |

**Returns:** the full `pathlib.Path`s of where subtitles were downloaded.

```python
# If the `dirname is None` then we can avoid an exception by either setting the
# `dirname` or specifying the `download_dir` for `download_subtitles`
assert downloads[0].media.dirname is None
downloads[0].media.dirname = "/path/to/subtitles"
download_paths = asw.download_subtitles(
    downloads, name_format="{upload_name}-{media_name}-{lang_2}.{ext}"
)
```

### `.get_comments(search_results)`

Get comments will get any of the comments people left on all the `search_results`.

| Param | Type | Description |
| :---: | :---: | :--- |
| `search_results` | [`List[SearchResult]`](#Custom-Classes.md#searchresult) | List of [`SearchResult`s](Custom-Classes.md#searchresult) to get comments for |


**Returns:** a list of lists of [`Comment`s](Custom-Classes.md#comment) (`List[List[Comment]]`) where each list is all the comments left on each [`SearchResult`](Custom-classes.md#searchresult).

```python
# Say we wanted to print out any of the comments left on the `search_results`
result_comments = asw.get_comments(search_results)
for result, comments in zip(search_results, result_comments):
    print(f"{result.media.name} Comments:")
    for comment in comments:
        print(f"{comment.author.name}: {comment.text}")
```

### `.guess_media(queries, ranking_func, *rank_args, **rank_kwargs)`

Tries to guess the movies or TV series that match the each of the `queries` strings.

| Param | Type | Description |
| :---: | :---: | :--- |
| `queries` | `List[str]` | The list of strings to guess media for |
| `ranking_func` | `function( results, query, *rank_args, **rank_kwargs ) -> best_result` | (Default `subwinder.ranking.rank_guess_media`) The function used to pick the "best" media from the returned guesses. This function takes the response returned for each query in `queries` that is formatted [as specified here](https://trac.opensubtitles.org/projects/opensubtitles/wiki/XMLRPC#GuessMovieFromString) along with the original `query` string and any `*rank_args` and `**rank_kwargs` passed in. The default just returns the one listed as `"BestGuess"`, but you can supply a custom function that follows this interface |
| `**rank_args` | `args` | (Default `[]`) The `args` passed to `ranking_func` |
| `**rank_kwargs` | `kwargs` | (Default `{}`) The `kwargs` passed to `ranking_func` |

**Returns:** a list of either [`MovieInfo`](Custom-Classes.md#movieinfo-derived-from-mediainfo) or [`TvSeriesInfo`](Custom-Classes.md#tvseriesinfo-derived-from-mediainfo) objects matching the guess for each query in `queries`.

```python
def custom_guess_media_ranking(results, query, guess_key="BestGuess"):
    return results[guess_key]


guesses = asw.get_comments(
    queries=["matrix reloaded", "aliens", "jojo rabbit"],
    ranking_func=custom_guess_media_ranking,
    guess_key="GuessMovieFromString",
)
```

### `.preview_subtitles(queries)`

Gets a preview for the given list of [`SearchResult`s](#Custom-Classes.md#searchresult). This can be used to try and determine the quality of subtitles before downloading them.

| Param | Type | Description |
| :---: | :---: | :--- |
| `queries` | [`List[SearchResult]`](Custom-Classes.md#searchresult) | The list of search results that you want to get previews for |

**Returns:** A `List[str]` where each string in the list is the corresponding preview for each [`SearchResult`](Custom-Classes.md#searchresult) given.

```python
# Want to get previews for `search_results`
previews = asw.preview_subtitles(search_results)

# Do something with each preview...
for preview in previews:
    pass
```

### `.ping()`

The API automatically logs users out after 15 minutes of no activity, so if you want to keep a session active, but have no work to do currently you can call this method every 15 minutes (or just start a new session later).

_No params, no return value_

```python
# Just keeps the session active
asw.ping()
```

### `.report_movie(search_result)`

**Note:** this can only be used for [`SearchResult`s](Custom-Classes.md#searchresult) that were found by searching with a [`Media`](Custom-Classes.md#media) object since it's tied to that specific file.

This is used to hint to the API that the subtitles for this [`SearchResult`](Custom-Classes.md#searchresult) are wrong for this specific [`Media`](Custom-Classes.md#media). They could be de-synchronized, list the wrong language, etc.. After some number of reports the hash will be removed from the database.

| Param | Type | Description |
| :---: | :---: | :--- |
| `search_result` | [`SearchResult`](Custom-Classes.md#searchresult) | The subtitles to report. This has to have been searched for using a [`Media`](Custom-Classes.md#media) object because reports are tied to the specific movie file |


```python
asw.report_movie(search_result)
```

### `.search_subtitles(queries, ranking_func, *rank_args, **rank_kwargs)`

Searches for subtitles for each query in `queries`. The API also limits the number of `queries` allowed, but again this library automatically batches the requests for you.

| Param | Type | Description |
| :---: | :---: | :--- |
| `queries` | [`List[Media or MovieInfo or EpisodeInfo]`](Custom-Classes.md) | The list of objects the you would like to search subtitles for |
| `ranking_func` | `function( results, query, *rank_args, **rank_kwargs ) -> best_result` | (Default `subwinder.ranking.rank_search_subtitles`) The function used to try and pick the best result of the results returned. This function takes the `results` returned by the API, the `query` that the results are returned for, and any `*rank_args` and `**rank_kwargs` passed in to return the "best" pick |
| `**rank_args` | `args` | (Default `[]`) The `args` passed to the `ranking_func` |
| `**rank_kwargs` | `kwargs` | (Default `{exclude_bad=True, sub_exts=None}`) Passed to `ranking_func` by default the ranking function picks the result with the highest `"Score"`. If `exclude_bad` is `True` then it will skip any subtitles that are listed as bad. `sub_exts` can be used to pass in a list of accepted formats such as `["srt", "ssa"]` |

**Returns:** a list of either [`SearchResult`](Custom-Classes.md#searchresult) or `None` representing the search result for each of the `queries`.

```python
def custom_search_subtitles_ranking(results, query, index=0):
    # Just return the result at `index` if it exists
    return results[index] if len(results) > index else None


search_results = asw.search_subtitles(
    queries, ranking_func=custom_search_subtitles_ranking, index=3
)
```

### `.suggest_media(query)`

Much like `guess_media` this attempts to guess the media for `query`. I'm honestly not sure how much it's use-case differs from that of `guess_media` other than only taking one query.

| Param | Type | Description |
| :---: | :---: | :--- |
| `query` | `str` | A string used to try to match some [`MediaInfo`](Custom-Classes.md#mediainfo) derivative |

**Returns:** a list of either [`MovieInfo`](Custom-Classes.md#movieinfo-derived-from-mediainfo) or [`TvSeriesInfo`](Custom-Classes.md#tvseries-derived-from-mediainfo) objects attempting to match the `query`.

```python
media_results = asw.suggest_media("matrix")
```

### `.user_info()`

Used to get info on the signed in user, it returns all the information provided in the [`FullUserInfo`](Custom-Classes.md#fulluserinfo-derived-from-userinfo) class.

**Returns:** the [`FullUserInfo`](Custom-Clases.md#fulluserinfo-derivde-from-userinfo) object for the signed in user.

```python
user_info = asw.user_info()
```

### `.vote(search_result, score)`

Add your vote with a score between 1 and 10 for the subtitles indicated by `search_result`

| Param | Type | Description |
| :---: | :---: | :--- |
| `search_result` | [`SearchResult`](Custom-Classes.md#searchresult) | The search result for the subtitles that you want to vote on |
| `score` | `int` | Rating between 1 and 10 that you give the subtitles |

```python
# Leave a good rating if the subtitles were good
asw.vote(search_result, 10)
```
