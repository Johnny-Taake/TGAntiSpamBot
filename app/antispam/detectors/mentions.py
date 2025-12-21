import re
from typing import Any

from app.antispam.dto import MessageTask
from app.antispam.detectors.text_normalizer import normalize_text


def _check_entity_type(entity: Any, target_types: set) -> bool:
    """Check if an entity is of any of the target types."""
    if isinstance(entity, dict):
        return entity.get("type") in target_types
    elif hasattr(entity, "type"):
        return getattr(entity, "type") in target_types
    return False


def has_mentions(task: MessageTask) -> bool:
    """
    Check if the message contains mentions.

    Args:
        task: Message task to check

    Returns:
        True if message contains mentions, False otherwise
    """
    text_raw = task.text or ""
    text = normalize_text(text_raw).lower().strip()

    # Entity-based detection (best when present)
    if task.entities:
        mention_types = {"mention"}
        for entity in task.entities:
            if _check_entity_type(entity, mention_types):
                return True

    # Text fallback (works even if entities are missing)
    # Telegram usernames: letters/digits/underscore, 5..32 chars typical
    if re.search(r"(?<!\w)@[a-zA-Z0-9_]{5,32}(?!\w)", text):
        return True

    return False
