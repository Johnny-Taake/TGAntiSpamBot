from app.antispam.dto import MessageTask
from app.antispam.detectors.text_normalizer import normalize_text
from app.antispam.detectors.shared import check_entity_type


def count_emojis(task: MessageTask) -> int:
    """
    Count the number of emojis in a message, including Telegram custom emojis.

    Args:
        task: Message task to check

    Returns:
        Number of emojis found in the message
    """
    text = normalize_text(task.text or "")

    # 1) Telegram Premium/custom emojis (entity-based)
    custom = 0
    if task.entities:
        for e in task.entities:
            if check_entity_type(e, {"custom_emoji"}):
                custom += 1

    def is_regional_indicator(cp: int) -> bool:
        return 0x1F1E6 <= cp <= 0x1F1FF

    def is_skin_tone(cp: int) -> bool:
        return 0x1F3FB <= cp <= 0x1F3FF

    def is_vs16(cp: int) -> bool:
        return cp == 0xFE0F

    def is_zwj(cp: int) -> bool:
        return cp == 0x200D

    # "Base emoji" heuristic
    def is_base_emoji(cp: int) -> bool:
        return (
            0x1F600 <= cp <= 0x1F64F or
            0x1F300 <= cp <= 0x1F5FF or
            0x1F680 <= cp <= 0x1F6FF or
            0x1F700 <= cp <= 0x1F77F or
            0x1F780 <= cp <= 0x1F7FF or
            0x1F800 <= cp <= 0x1F8FF or
            0x1F900 <= cp <= 0x1F9FF or
            0x1FA70 <= cp <= 0x1FAFF or
            0x2600 <= cp <= 0x27BF
        )

    i = 0
    n = len(text)
    unicode_count = 0

    while i < n:
        cp = ord(text[i])

        # Flags: two regional indicators count as one emoji
        if is_regional_indicator(cp):
            if i + 1 < n and is_regional_indicator(ord(text[i + 1])):
                unicode_count += 1
                i += 2
                continue
            # single RI -> treat as emoji-ish
            unicode_count += 1
            i += 1
            continue

        # Start only on a base emoji
        if not is_base_emoji(cp):
            i += 1
            continue

        unicode_count += 1
        i += 1

        # Optional VS16 + skin tone
        if i < n and is_vs16(ord(text[i])):
            i += 1
        if i < n and is_skin_tone(ord(text[i])):
            i += 1

        # ZWJ sequences: (ZWJ + base + [VS16] + [skin]) repeated
        while i < n and is_zwj(ord(text[i])):
            # consume ZWJ
            i += 1
            if i >= n:
                break
            # next must be a base emoji to continue sequence
            if not is_base_emoji(ord(text[i])):
                break
            i += 1
            if i < n and is_vs16(ord(text[i])):
                i += 1
            if i < n and is_skin_tone(ord(text[i])):
                i += 1

    return custom + unicode_count


def has_excessive_emojis(task: MessageTask, max_emojis: int) -> bool:
    """
    Check if the message has more emojis than allowed.

    Args:
        task: Message task to check
        max_emojis: Maximum allowed emojis

    Returns:
        True if message has more emojis than allowed, False otherwise
    """
    emoji_count = count_emojis(task)
    return emoji_count > max_emojis
