"""
Performance optimized database services for chat and user state operations
"""

from typing import Optional, Dict
import time
from threading import Lock

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Chat


class CachedChatService:
    """
    A service that caches chat lookups to reduce database queries.
    """

    def __init__(self, cache_ttl: int = 300):
        self._cache: Dict[
            int, tuple[Chat, float]
        ] = {}  # {chat_id: (chat_obj, timestamp)}
        self._cache_ttl = cache_ttl
        self._lock = Lock()

    def _cleanup_expired(self):
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = []

        for chat_id, (_, timestamp) in self._cache.items():
            if current_time - timestamp > self._cache_ttl:
                expired_keys.append(chat_id)

        for chat_id in expired_keys:
            del self._cache[chat_id]

    def _get_cached_chat(self, telegram_chat_id: int) -> Optional[Chat]:
        """Get a chat from cache if available and not expired."""
        with self._lock:
            if telegram_chat_id in self._cache:
                chat, timestamp = self._cache[telegram_chat_id]
                if time.time() - timestamp <= self._cache_ttl:
                    return chat
                else:
                    # Remove expired entry
                    del self._cache[telegram_chat_id]
            return None

    def _set_cached_chat(self, chat: Chat):
        """Cache a chat object."""
        with self._lock:
            self._cleanup_expired()
            self._cache[chat.telegram_chat_id] = (chat, time.time())

    def invalidate_chat(self, telegram_chat_id: int):
        """Invalidate a specific chat from cache."""
        with self._lock:
            if telegram_chat_id in self._cache:
                del self._cache[telegram_chat_id]

    def invalidate_all(self):
        """Invalidate all cached chats."""
        with self._lock:
            self._cache.clear()

    async def get_chat_by_telegram_id(
        self, session: AsyncSession, telegram_chat_id: int
    ) -> Optional[Chat]:
        """Get chat by telegram ID with caching."""
        # Check cache first
        cached_chat = self._get_cached_chat(telegram_chat_id)
        if cached_chat:
            return cached_chat

        # Query database if not in cache
        stmt = select(Chat).where(Chat.telegram_chat_id == telegram_chat_id)
        res = await session.execute(stmt)
        chat = res.scalar_one_or_none()

        if chat:
            self._set_cached_chat(chat)

        return chat


cached_chat_service = CachedChatService()


async def get_chat_by_telegram_id(
    session: AsyncSession, telegram_chat_id: int
) -> Optional[Chat]:
    """
    Get a chat by telegram ID using cached retrieval.
    """
    return await cached_chat_service.get_chat_by_telegram_id(session, telegram_chat_id)
