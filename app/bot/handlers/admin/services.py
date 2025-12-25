from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import Chat
from logger import get_logger

log = get_logger(__name__)


async def fetch_group_chats(session: AsyncSession) -> list[Chat]:
    result = await session.execute(
        select(Chat).where(Chat.telegram_chat_id < 0)
    )
    return list(result.scalars().all())


async def update_chat_titles(
    session: AsyncSession,
    bot: Bot,
    chats: list[Chat],
) -> None:
    updated = False

    for chat in chats:
        if not chat.title or chat.title == f"Chat {chat.telegram_chat_id}":
            try:
                chat_obj = await bot.get_chat(chat.telegram_chat_id)
                title = getattr(chat_obj, "title", None)
                if title and title != chat.title:
                    chat.title = title
                    updated = True
            except Exception:
                continue

    if updated:
        await session.commit()


async def ensure_chat_link(
    session: AsyncSession,
    bot: Bot,
    chat: Chat,
) -> tuple[bool, str]:
    try:
        chat_obj = await bot.get_chat(chat.telegram_chat_id)
        username = getattr(chat_obj, "username", None)

        if username:
            link = f"https://t.me/{username}"
            if chat.chat_link != link:
                chat.chat_link = link
                await session.commit()
            return True, "Saved public link ↗️"

        invite = await bot.create_chat_invite_link(
            chat_id=chat.telegram_chat_id,
            name="Admin panel link",
            creates_join_request=False,
        )
        chat.chat_link = invite.invite_link
        await session.commit()
        return True, "Invite link created ↗️"

    except Exception as e:
        log.warning(
            "ensure_chat_link failed chat=%s err=%s",
            chat.telegram_chat_id,
            e,
        )
        return False, "Can't create link"
