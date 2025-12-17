"""
Timezone utility functions to handle common timezone operations.
"""

from datetime import datetime, timezone


def ensure_utc_timezone(dt: datetime) -> datetime:
    """
    Ensure a datetime object has UTC timezone information.

    Args:
        dt: The datetime object to ensure has UTC timezone

    Returns:
        A datetime object with UTC timezone
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def utc_now() -> datetime:
    """
    Get the current time in UTC timezone.

    Returns:
        Current datetime with UTC timezone
    """
    return datetime.now(timezone.utc)
