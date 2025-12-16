from typing import Any

from aiogram import Router, Bot, types
from aiogram.enums import ChatType
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.db.models.chat import Chat
from app.antispam import AntiSpamService, MessageTask
from logger import get_logger
from config import config

log = get_logger(__name__)
router = Router()


@router.message()
async def anti_spam_stub(
    message: types.Message,
    bot: Bot,
    session: AsyncSession,
    antispam: AntiSpamService,
    **kwargs: Any,
):
    log.debug(
        "anti_spam_stub: chat_id=%s chat_type=%s msg_id=%s from_user=%s",
        message.chat.id,
        message.chat.type,
        message.message_id,
        message.from_user.id if message.from_user else None,
    )

    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        log.debug("Message not from group/supergroup, skipping: %s", message.chat.type)
        return

    stmt = select(Chat).where(Chat.telegram_chat_id == message.chat.id)
    result = await session.execute(stmt)
    chat = result.scalar_one_or_none()

    incoming_title = (getattr(message.chat, "title", None) or "").strip() or None

    log.debug("Chat lookup result for %s - exists: %s", message.chat.id, chat is not None)

    if not chat:
        try:
            chat = Chat(
                telegram_chat_id=message.chat.id,
                title=incoming_title,
                is_active=False,
            )
            session.add(chat)
            await session.commit()
            log.info("Chat created from message fallback: %s (%r)", message.chat.id, incoming_title)
        except IntegrityError:
            await session.rollback()
            result = await session.execute(stmt)
            chat = result.scalar_one_or_none()
            log.debug("Race condition handled for chat creation, retrieved existing: %s", message.chat.id if chat else "None")
    else:
        if incoming_title and chat.title != incoming_title:
            old_title = chat.title
            chat.title = incoming_title
            await session.commit()
            log.info("Updated chat title: %s - %r -> %r", message.chat.id, old_title, incoming_title)
        elif not chat.title and incoming_title:
            chat.title = incoming_title
            await session.commit()
            log.info("Set initial chat title: %s - %r", message.chat.id, incoming_title)

    if not message.from_user:
        log.debug("Skipping anti-spam for anonymous admin message: %s", message.message_id)
        return

    if message.from_user.id == config.bot.main_admin_id:
        log.debug("Skipping anti-spam for main admin message: %s from user %s",
                 message.message_id, message.from_user.id)
        return

    text = message.text or message.caption or ""
    entities = (message.entities or []) + (message.caption_entities or [])

    task = MessageTask(
        telegram_chat_id=message.chat.id,
        telegram_message_id=message.message_id,
        telegram_user_id=message.from_user.id,
        text=text,
        entities=[e.model_dump() for e in entities],
        chat_title=incoming_title,
    )

    log.debug("Enqueuing anti-spam task for chat %s, message %s from user %s",
             message.chat.id, message.message_id, message.from_user.id)

    await antispam.enqueue(task)
