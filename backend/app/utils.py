import unicodedata


def remove_accents(text: str) -> str:
    """
    Returns the string without any accents.
    """

    if not text:
        return ""

    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def normalize_search_query(text: str | None) -> str:
    """
    Normalizes a search term for accent-insensitive fuzzy matching:
    trims whitespace, lowercases and strips accents/diacritics.
    """

    if not text:
        return ""

    return remove_accents(text.strip().lower())
