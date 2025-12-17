from sqlalchemy.ext.asyncio import AsyncSession

from app.db import UserState
from utils import get_or_create


async def get_or_create_user_state(
    session: AsyncSession,
    chat_id: int,
    telegram_user_id: int,
) -> UserState:
    user_state, _ = await get_or_create(
        session,
        UserState,
        chat_id=chat_id,
        telegram_user_id=telegram_user_id,
    )
    return user_state
