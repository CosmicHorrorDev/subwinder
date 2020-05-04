def rank_guess_media(results, query):
    """
    The default ranking function used to determine the best result for `AuthSubwinder`'s
    `.guess_media(...)` method. `results` is the information returned as specified by
    trac.opensubtitles.org/projects/opensubtitles/wiki/XMLRPC#GuessMovieFromString
    and `query` is the original `str` being guessed.
    """
    return results["BestGuess"]


def rank_search_subtitles(results, query, exclude_bad=True, sub_exts=None):
    """
    The default ranking function used to determine the best result for `AuthSubwinder`'s
    `.search_subtitles(...)` method. `results` is the information returned as specified
    by https://trac.opensubtitles.org/projects/opensubtitles/wiki/XMLRPC#SearchSubtitles
    `query` is the object passed in to search for. `exclude_bad` just skips any result
    that has been marked as bad by a user, and `sub_exts` is an optional
    case-insensitive list of accepted subtitle extensions.
    """
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
