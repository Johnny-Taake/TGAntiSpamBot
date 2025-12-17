from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class MessageTask:
    telegram_chat_id: int
    telegram_message_id: int
    telegram_user_id: int

    text: Optional[str] = None
    entities: list[dict[str, Any]] = field(default_factory=list)

    chat_title: Optional[str] = None
