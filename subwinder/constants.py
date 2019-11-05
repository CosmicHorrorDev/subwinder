_API_BASE = "https://api.opensubtitles.org/xml-rpc"

_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

_REPO_URL = "https://github.com/LovecraftianHorror/subwinder"

_LANG_TEMP = [
    ("afr", "af"),  # Afrikaans
    ("alb", "sq"),  # Albanian
    ("ara", "ar"),  # Arabic
    ("arg", "an"),  # Aragonese
    ("arm", "hy"),  # Armenian
    ("aze", "az"),  # Azerbaijani
    ("baq", "eu"),  # Basque
    ("bel", "be"),  # Belarusian
    ("ben", "bn"),  # Bengali
    ("bos", "bs"),  # Bosnian
    ("bre", "br"),  # Breton
    ("bul", "bg"),  # Bulgarian
    ("bur", "my"),  # Burmese
    ("cat", "ca"),  # Catalan; Valencian
    ("chi", "zh"),  # Chinese
    ("hrv", "hr"),  # Croatian
    ("cze", "cs"),  # Czech
    ("dan", "da"),  # Danish
    ("dut", "nl"),  # Dutch; Flemish
    ("eng", "en"),  # English
    ("epo", "eo"),  # Esperanto
    ("est", "et"),  # Estonian
    ("fin", "fi"),  # Finnish
    ("fre", "fr"),  # French
    ("gla", "gd"),  # Gaelic; Scottish Gaelic
    ("glg", "gl"),  # Galician
    ("geo", "ka"),  # Georgian
    ("ger", "de"),  # German
    ("ell", "el"),  # Greek
    ("heb", "he"),  # Hebrew
    ("hin", "hi"),  # Hindi
    ("hun", "hu"),  # Hungarian
    ("ice", "is"),  # Icelandic
    ("ibo", "ig"),  # Igbo
    ("ind", "id"),  # Indonesian
    ("gle", "ga"),  # Irish
    ("ita", "it"),  # Italian
    ("jpn", "ja"),  # Japanese
    ("kan", "kn"),  # Kannada
    ("kaz", "kk"),  # Kazakh
    ("khm", "km"),  # Central Khmer
    ("kor", "ko"),  # Korean
    ("kur", "ku"),  # Kurdish
    ("lav", "lv"),  # Latvian
    ("lit", "lt"),  # Lithuanian
    ("ltz", "lb"),  # Luxembourgish; Letzeburgesch
    ("mac", "mk"),  # Macedonian
    ("may", "ms"),  # Malay
    ("mal", "ml"),  # Malayalam
    ("mon", "mn"),  # Mongolian
    ("sme", "se"),  # Northern Sami
    ("nor", "no"),  # Norwegian
    ("oci", "oc"),  # Occitan
    ("per", "fa"),  # Persian
    ("pol", "pl"),  # Polish
    ("por", "pt"),  # Portuguese
    ("rum", "ro"),  # Romanian; Moldavian; Moldovan
    ("rus", "ru"),  # Russian
    ("scc", "sr"),  # Serbian
    ("snd", "sd"),  # Sindhi
    ("sin", "si"),  # Sinhala; Sinhalese
    ("slo", "sk"),  # Slovak
    ("slv", "sl"),  # Slovenian
    ("som", "so"),  # Somali
    ("spa", "es"),  # Spanish
    ("swe", "sv"),  # Swedish
    ("tha", "th"),  # Thai
    ("tur", "tr"),  # Turkish
    ("ukr", "uk"),  # Ukranian
    ("urd", "ur"),  # Urdu
    ("vie", "vi"),  # Vietnamese
]

_LANG_2 = set([lang_2 for _, lang_2 in _LANG_TEMP])
_LANG_3_TO_2 = dict(_LANG_TEMP)
_LANG_2_TO_3 = {lang_2: lang_3 for lang_3, lang_2 in _LANG_TEMP}

del _LANG_TEMP
