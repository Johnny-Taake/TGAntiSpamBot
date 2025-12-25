import re
from typing import Any

from app.antispam.dto import MessageTask
from app.antispam.detectors.text_normalizer import normalize_text
from app.antispam.detectors.shared import check_entity_type
from app.db.models.chat import Chat
from utils import extract_domains_from_text
from utils import normalize_host


def has_links(task: MessageTask, chat: Chat = None) -> bool:
    """
    Check if the message contains links.
    If chat is provided, checks against the allowed link domains whitelist.

    Args:
        task: Message task to check
        chat: Chat object containing allowed domains whitelist (optional)

    Returns:
        True if message contains links (not in whitelist), False otherwise
    """
    text_raw = task.text or ""
    text = normalize_text(text_raw).lower().strip()

    allowed = (
        {normalize_host(d) for d in (chat.allowed_link_domains or [])}
        if chat
        else set()
    )

    if task.entities:
        link_types = {"url", "text_link"}
        for entity in task.entities:
            if not check_entity_type(entity, link_types):
                continue

            ent_type = (
                getattr(entity, "type", None)
                if not isinstance(entity, dict)
                else entity.get("type")
            )

            if ent_type == "text_link":
                link_value = (
                    getattr(entity, "url", None)
                    if not isinstance(entity, dict)
                    else entity.get("url")
                )
            else:
                link_value = extract_entity_text(text_raw, entity)

            if link_value:
                domains = extract_domains_from_text(link_value)
                if chat and allowed and domains and domains.issubset(allowed):
                    continue
            return True

    domains = extract_domains_from_text(text_raw)
    if domains:
        if chat and allowed and domains.issubset(allowed):
            return False
        return True

    if re.search(r"[a-zA-Z][a-zA-Z0-9+.-]*://|www\.|t\.me/", text):
        if chat and allowed:
            domains2 = extract_domains_from_text(text)
            if domains2 and domains2.issubset(allowed):
                return False
        return True

    return False


def extract_entity_text(full_text: str, entity: Any) -> str:
    try:
        offset = (
            entity.get("offset", 0)
            if isinstance(entity, dict)
            else getattr(entity, "offset", 0)
        )
        length = (
            entity.get("length", 0)
            if isinstance(entity, dict)
            else getattr(entity, "length", 0)
        )
        if (
            offset is not None
            and length is not None
            and offset + length <= len(full_text)
        ):
            return full_text[offset: offset + length]
        return ""
    except Exception:
        return ""
