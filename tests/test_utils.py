from subwinder.utils import extract


def test_extract():
    COMPRESSED = (
        "H4sIAIXHxV0C/yXLwQ0CMQxE0VbmxoVCoAyzHiBS4lnFXtB2TyRuT/r6N/Yu1JuTV9wvY"
        "9EKL8mhTmwa+2QmHRYOxiZfzuNRrVZv8dQcVk3xP08dSMFps5/4WhRKSPvwBzf2OXZqAA"
        "AA"
    )
    IDEAL = (
        "Hello there, I'm that good ole compressed and encoded subtitle"
        " information that you so dearly want to save"
    )

    assert extract(COMPRESSED, "UTF-8") == IDEAL
