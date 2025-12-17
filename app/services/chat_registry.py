import time
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.db.models.chat import Chat
from app.services import get_chat_by_telegram_id
from logger import get_logger


log = get_logger(__name__)


@dataclass
class ChatCacheEntry:
    last_seen_ts: float
    title: Optional[str]


class ChatRegistry:
    """
    In-memory cache to avoid DB hits on every message.
    Cache key: telegram_chat_id
    """

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl = ttl_seconds
        self._cache: dict[int, ChatCacheEntry] = {}

    def _is_fresh(self, chat_id: int) -> bool:
        e = self._cache.get(chat_id)
        return bool(e and (time.time() - e.last_seen_ts) < self.ttl)

    def touch(self, chat_id: int, title: Optional[str]) -> None:
        self._cache[chat_id] = ChatCacheEntry(last_seen_ts=time.time(), title=title)
        log.debug("Cache entry updated: chat_id=%s, title=%r", chat_id, title)

    async def ensure_chat(
        self,
        session: AsyncSession,
        telegram_chat_id: int,
        title: Optional[str],
        default_is_active: bool = False,
    ) -> None:
        # If we saw this chat recently, skip DB entirely
        if self._is_fresh(telegram_chat_id):
            log.debug("Chat cache hit: telegram_chat_id=%s", telegram_chat_id)
            return

        log.debug("Chat cache miss: telegram_chat_id=%s, checking DB", telegram_chat_id)  # noqa: E501
        chat = await get_chat_by_telegram_id(session, telegram_chat_id)
        if chat is None:
            try:
                log.info(
                    "Creating new chat: telegram_chat_id=%s title=%r is_active=%s",  # noqa: E501
                    telegram_chat_id,
                    title,
                    default_is_active,
                )
                chat = Chat(
                    telegram_chat_id=telegram_chat_id,
                    title=title,
                    is_active=default_is_active,
                )
                session.add(chat)
                await session.flush()
                await session.commit()
                log.info(
                    "Successfully created chat: telegram_chat_id=%s", telegram_chat_id  # noqa: E501
                )
            except IntegrityError:
                log.warning(
                    "Chat creation race condition: telegram_chat_id=%s already exists",  # noqa: E501
                    telegram_chat_id,
                )
                await session.rollback()
        else:
            if title and title != (chat.title or None):
                log.info(
                    "Updating chat title: telegram_chat_id=%s old=%r new=%r",  # noqa: E501
                    telegram_chat_id,
                    chat.title,
                    title,
                )
                chat.title = title
                await session.commit()

        self.touch(telegram_chat_id, title)
