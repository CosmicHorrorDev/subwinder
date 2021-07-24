from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, NewType, Tuple, Union

if TYPE_CHECKING:
    from subwinder.info import Episode, Media, Movie, SearchResult, Subtitles

Lang2 = NewType("Lang2", str)
Lang3 = NewType("Lang3", str)
LangLong = NewType("LangLong", str)

Token = NewType("Token", str)

Searchable = Union["Media", "Movie", "Episode"]
SearchQuery = Tuple[Searchable, Lang2]

SubContainer = Union["SearchResult", "Subtitles"]

ApiObj = Dict[str, Any]

AnyPath = Union[str, Path]
