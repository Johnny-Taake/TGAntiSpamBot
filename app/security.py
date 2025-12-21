"""
Security utilities for input validation and sanitization
"""

from typing import Optional


def sanitize_text(text: Optional[str]) -> str:
    """
    Sanitizes text input to prevent potential security issues.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text string
    """
    if not text or not isinstance(text, str):
        return ""

    # Remove null bytes and other dangerous characters
    sanitized = text.replace("\x00", "")

    return sanitized[:12000]  # Limit to 12k characters
