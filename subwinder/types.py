from typing import Tuple, Union

from subwinder.info import Episode, Media, Movie, SearchResult, Subtitles

Lang2 = str
Lang3 = str
LangLong = str

Token = str

Searchable = Union[Media, Movie, Episode]
SearchQuery = Tuple[Searchable, Lang2]

SubContainer = Union[SearchResult, Subtitles]
