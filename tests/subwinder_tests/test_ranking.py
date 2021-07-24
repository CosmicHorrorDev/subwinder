from subwinder.ranking import rank_guess_media, rank_search_subtitles
from tests.constants import (
    GUESS_MEDIA_RESULT,
    MOVIE_INFO1,
    SEARCH_RESULT1,
    SEARCH_RESULT2,
)


def test_rank_guess_media():
    assert rank_guess_media(GUESS_MEDIA_RESULT, "dummy query") == MOVIE_INFO1


def test_rank_search_subtitles():
    DUMMY_RESULTS = [
        SEARCH_RESULT1,
        SEARCH_RESULT2,
    ]

    # Empty results means nothing matched the query
    assert rank_search_subtitles([], MOVIE_INFO1) is None
    # Exludes `SEARCH_RESULT1` because it's _bad_
    assert rank_search_subtitles(DUMMY_RESULTS, MOVIE_INFO1) == SEARCH_RESULT2
    # Prefers `SEARCH_RESULT1` because there's a higher score
    assert (
        rank_search_subtitles(DUMMY_RESULTS, MOVIE_INFO1, exclude_bad=False)
        == SEARCH_RESULT1
    )
    # Excludes `SEARCH_RESULT1` because of format
    assert (
        rank_search_subtitles(DUMMY_RESULTS, MOVIE_INFO1, sub_exts=["SRT"])
        == SEARCH_RESULT2
    )
    # `None` when nothing matches
    assert rank_search_subtitles(DUMMY_RESULTS, MOVIE_INFO1, sub_exts=["ass"]) is None
