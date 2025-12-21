from sqlalchemy.ext.asyncio import AsyncSession

from app.db import UserState
from utils import get_or_create
from logger import get_logger

log = get_logger(__name__)


async def get_or_create_user_state(
    session: AsyncSession,
    chat_id: int,
    telegram_user_id: int,
) -> UserState:
    log.debug("Getting or creating user state for chat_id=%s, telegram_user_id=%s", chat_id, telegram_user_id)
    user_state, created = await get_or_create(
        session,
        UserState,
        chat_id=chat_id,
        telegram_user_id=telegram_user_id,
    )
    if created:
        log.debug("Created new user state for chat_id=%s, telegram_user_id=%s", chat_id, telegram_user_id)
    else:
        log.debug("Retrieved existing user state for chat_id=%s, telegram_user_id=%s", chat_id, telegram_user_id)
    return user_state
