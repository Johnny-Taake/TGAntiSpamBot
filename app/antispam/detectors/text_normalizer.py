import re


def normalize_text(s: str) -> str:
    """
    Remove invisible unicode often used in obfuscation

    Args:
        s: Input text to normalize

    Returns:
        Normalized text with invisible unicode removed
    """
    return re.sub(r"[\u200b-\u200f\u2060\ufeff]", "", s)
