"""
Input validation and basic text sanitization utilities
"""

from typing import Optional


def sanitize_text(text: Optional[str]) -> str:
    """
    Performs basic text sanitization - removes null bytes and truncates length.

    Args:
        text: Text to sanitize

    Returns:
        Basic sanitized text string
    """
    if not text or not isinstance(text, str):
        return ""

    # Remove null bytes which can cause database issues
    sanitized = text.replace("\x00", "")

    return sanitized[:12000]  # Limit to 12k characters
