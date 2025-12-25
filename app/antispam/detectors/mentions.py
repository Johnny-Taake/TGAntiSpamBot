import re

from app.antispam.dto import MessageTask
from app.antispam.detectors.text_normalizer import normalize_text
from app.antispam.detectors.shared import check_entity_type


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
            if check_entity_type(entity, mention_types):
                return True

    # Text fallback (works even if entities are missing)
    # Telegram usernames: letters/digits/underscore, 5..32 chars typical
    if re.search(r"(?<!\w)@[a-zA-Z0-9_]{5,32}(?!\w)", text):
        return True

    return False
