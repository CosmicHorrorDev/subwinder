from subwinder.ranking import _rank_search_subtitles


def test__rank_search_subtitles():
    DUMMY_RESULTS = [
        {"SubBad": "1", "SubFormat": "ASS", "Score": 105.0},
        {"SubBad": "0", "SubFormat": "Srt", "Score": 100.0},
    ]

    # Format is (<args>, <kwargs>, <result>)
    PARAM_TO_IDEAL_RESULT = [
        # Empty results means nothing matched the query
        (([], 0), {}, None),
        # Exludes `DUMMY_RESULTS[0]` because it's _bad_
        ((DUMMY_RESULTS, 0), {}, DUMMY_RESULTS[1]),
        # Prefers `DUMMY_RESULTS[0]` because there's more downloads
        ((DUMMY_RESULTS, 0), {"exclude_bad": False}, DUMMY_RESULTS[0]),
        # Ecludes `DUMMY_RESULTS[0]` because of format
        ((DUMMY_RESULTS, 0), {"sub_exts": ["SRT"]}, DUMMY_RESULTS[1]),
        # What happens when nothing matches the parameters?
        (
            (DUMMY_RESULTS, 0),
            {"exclude_bad": True, "sub_exts": ["ass"]},
            None,
        ),
    ]

    for args, kwargs, ideal_result in PARAM_TO_IDEAL_RESULT:
        assert _rank_search_subtitles(*args, **kwargs) == ideal_result
