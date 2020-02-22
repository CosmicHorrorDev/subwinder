def _rank_guess_media(results, query):
    return results["BestGuess"]


def _rank_search_subtitles(results, query, exclude_bad=True, sub_exts=None):
    best_result = None
    max_score = None

    # Force list of `sub_exts` to be lowercase
    sub_exts = None if sub_exts is None else [ext.lower() for ext in sub_exts]

    for result in results:
        # Skip if someone listed sub as bad and `exclude_bad` is `True`
        if exclude_bad and result["SubBad"] != "0":
            continue

        # Skip incorrect `sub_ext`s if provided
        if sub_exts is not None and result["SubFormat"].lower() not in sub_exts:
            continue

        if max_score is None or result["Score"] > max_score:
            best_result = result
            max_score = result["Score"]

    return best_result
