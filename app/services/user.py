from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.user_state import UserState


async def get_or_create_user_state(
    session: AsyncSession,
    chat_id: int,
    telegram_user_id: int,
) -> UserState:
    stmt = select(UserState).where(
        UserState.chat_id == chat_id,
        UserState.telegram_user_id == telegram_user_id,
    )
    result = await session.execute(stmt)
    user_state = result.scalar_one_or_none()

    if user_state:
        return user_state

    from sqlalchemy.exc import IntegrityError
    try:
        user_state = UserState(
            chat_id=chat_id,
            telegram_user_id=telegram_user_id,
        )
        session.add(user_state)
        await session.flush()
        return user_state
    except IntegrityError:
        # Handle race condition where another worker created the same user state
        await session.rollback()
        stmt = select(UserState).where(
            UserState.chat_id == chat_id,
            UserState.telegram_user_id == telegram_user_id,
        )
        result = await session.execute(stmt)
        existing_user_state = result.scalar_one_or_none()
        if existing_user_state:
            return existing_user_state
        else:
            raise
