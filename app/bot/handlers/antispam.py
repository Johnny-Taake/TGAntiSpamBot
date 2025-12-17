from typing import Any

from aiogram import Router, types
from sqlalchemy.ext.asyncio import AsyncSession

from app.antispam import AntiSpamService, MessageTask
from app.bot.filters import GroupOrSupergroupChatFilter
from app.services.chat_registry import ChatRegistry
from config import config
from logger import get_logger

log = get_logger(__name__)

router = Router()


@router.message(GroupOrSupergroupChatFilter())
async def anti_spam_stub(
    message: types.Message,
    antispam: AntiSpamService,
    session: AsyncSession,
    chat_registry: ChatRegistry,
    **kwargs: Any,
):
    if not message.from_user:
        return

    incoming_title = (getattr(message.chat, "title", None) or "").strip() or None  # noqa: E501

    log.debug(
        "Processing message from user_id=%s in chat_id=%s (admin=%s)",  # noqa: E501
        message.from_user.id,
        message.chat.id,
        message.from_user.id == config.bot.main_admin_id,
    )

    await chat_registry.ensure_chat(
        session=session,
        telegram_chat_id=message.chat.id,
        title=incoming_title,
        default_is_active=False,
    )

    if message.from_user.id == config.bot.main_admin_id:
        log.debug("Skipping antispam for admin user_id=%s", message.from_user.id)  # noqa: E501
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

    log.debug(
        "Enqueuing antispam task: chat_id=%s msg_id=%s user_id=%s",  # noqa: E501
        message.chat.id,
        message.message_id,
        message.from_user.id,
    )
    await antispam.enqueue(task)
