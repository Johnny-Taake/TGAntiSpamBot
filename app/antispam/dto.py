from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class MessageTask:
    telegram_chat_id: int
    telegram_message_id: int
    telegram_user_id: int

    text: Optional[str] = None
    entities: list[dict[str, Any]] = None

    chat_title: Optional[str] = None

    def __post_init__(self):
        # Set default value for entities if not provided
        if self.entities is None:
            object.__setattr__(self, 'entities', [])
