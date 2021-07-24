from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, NewType, Tuple, Union

if TYPE_CHECKING:
    from subwinder.info import Episode, Movie, SearchResult, Subtitles
    from subwinder.media import MediaFile

Token = NewType("Token", str)

Lang2 = str
Lang3 = str
LangLong = str

Searchable = Union["MediaFile", "Movie", "Episode"]
SearchQuery = Tuple[Searchable, Lang2]

SubContainer = Union["SearchResult", "Subtitles"]

ApiDict = Dict[str, Any]

AnyPath = Union[str, Path]
