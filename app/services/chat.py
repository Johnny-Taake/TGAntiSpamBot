from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Chat


async def get_chat_by_telegram_id(
    session: AsyncSession, telegram_chat_id: int
) -> Optional[Chat]:
    stmt = select(Chat).where(Chat.telegram_chat_id == telegram_chat_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()
