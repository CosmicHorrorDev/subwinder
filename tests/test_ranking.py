from subwinder.ranking import rank_guess_media, rank_search_subtitles
from tests.constants import (
    GUESS_MEDIA_RESULT,
    MOVIE_INFO1,
    SEARCH_RESULT1,
    SEARCH_RESULT2,
)


def test_rank_guess_media():
    assert rank_guess_media(GUESS_MEDIA_RESULT, None) == MOVIE_INFO1


def test_rank_search_subtitles():
    DUMMY_RESULTS = [
        SEARCH_RESULT1,
        SEARCH_RESULT2,
    ]

    # Format is (<args>, <kwargs>, <result>)
    PARAM_TO_IDEAL_RESULT = [
        # Empty results means nothing matched the query
        (([], 0), {}, None),
        # Exludes `DUMMY_RESULTS[0]` because it's _bad_
        ((DUMMY_RESULTS, 0), {}, DUMMY_RESULTS[1]),
        # Prefers `DUMMY_RESULTS[0]` because there's a higher score
        ((DUMMY_RESULTS, 0), {"exclude_bad": False}, DUMMY_RESULTS[0]),
        # Ecludes `DUMMY_RESULTS[0]` because of format
        ((DUMMY_RESULTS, 0), {"sub_exts": ["SRT"]}, DUMMY_RESULTS[1]),
        # What happens when nothing matches the parameters?
        ((DUMMY_RESULTS, 0), {"exclude_bad": True, "sub_exts": ["ass"]}, None,),
    ]

    for args, kwargs, ideal_result in PARAM_TO_IDEAL_RESULT:
        assert rank_search_subtitles(*args, **kwargs) == ideal_result
