from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chat, ChatAdmin


async def get_chat_by_telegram_id(
    session: AsyncSession, telegram_chat_id: int
) -> Optional[Chat]:
    stmt = select(Chat).where(Chat.telegram_chat_id == telegram_chat_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def get_admin_chats(
    session: AsyncSession,
    admin_telegram_id: int,
):
    stmt = (
        select(Chat)
        .join(Chat.admins)
        .where(ChatAdmin.telegram_user_id == admin_telegram_id)
        .order_by(Chat.title)
    )
    res = await session.execute(stmt)
    return res.scalars().all()
