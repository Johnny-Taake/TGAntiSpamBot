from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Chat
from logger import get_logger

log = get_logger(__name__)


async def get_chat_by_telegram_id(
    session: AsyncSession, telegram_chat_id: int
) -> Optional[Chat]:
    stmt = select(Chat).where(Chat.telegram_chat_id == telegram_chat_id)
    res = await session.execute(stmt)
    chat = res.scalar_one_or_none()
    if chat:
        log.debug("Found chat with telegram_chat_id=%s", telegram_chat_id)
    else:
        log.debug("No chat found with telegram_chat_id=%s", telegram_chat_id)
    return chat
