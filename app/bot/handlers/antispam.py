from typing import Any

from aiogram import Router, types
from aiogram.enums import ChatType

from app.antispam import AntiSpamService, MessageTask
from config import config

router = Router()


@router.message()
async def anti_spam_stub(
    message: types.Message,
    antispam: AntiSpamService,
    **kwargs: Any,
):
    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    if not message.from_user:
        return

    if message.from_user.id == config.bot.main_admin_id:
        return

    incoming_title = (getattr(message.chat, "title", None) or "").strip() or None
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

    await antispam.enqueue(task)
