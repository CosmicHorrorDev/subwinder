**This is still heavily a work in progress for an ergonomic [opensubtitles.org](https://opensubtitles.org) python wrapper. Many aspects won't work correctly yet, give it a couple months**

The final goal of the design is to be able to write code something like this

```python
from subwinder import AuthSubWinder, Movie, Subtitles

# Design Goals
# Setting up our initial `AuthSubWinder` `Movie` and `Subtitles` objects
movie = Movie.from_file("/path/to/movie.mkv")
subs = Subtitles("/path/to/movie.deu.srt")
with AuthSubWinder("<username>", "<password>", "<useragent>") as sw:
    # Method that needs both a `Movie` and `Subtitles` object
    # still not sure quite how this will work yet
    sw.upload_subtitles(movie, subs, ...)

    # Methods that need a `Movie` object
    sw.subscribe(movie)
    en_movie_result, es_movie_result = sw.search_movies([(movie, "en"),
                                                         (movie, "es")])
    sw.download([en_movie_result, es_movie_result])

    # Method that needs just a `SearchResult` object
    sw.report_wrong_movie(en_movie_result)

    # Method that needs just `Subtitles` objects
    subs_result = sw.check_subtitles([subs])[0]

    # Methods that could take either a `SearchResult` or `SubtitlesResult`
    sw.vote(subs_result, 10)
    # TODO: these take subtitleid not subtitlefileid which makes life harder
    sw.add_comment(subs_result, "Subs were great, thanks!")
    comments = sw.get_comments(en_movie_result)
```
