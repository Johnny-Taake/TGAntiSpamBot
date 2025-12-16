from typing import Any

from aiogram import Router, Bot, types
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from logger import get_logger

log = get_logger(__name__)
router = Router()


def _has_mentions_or_links(message: types.Message) -> bool:
    text = message.text or message.caption or ""
    if not text:
        return False

    if "http://" in text or "https://" in text or "t.me/" in text or "www." in text:
        return True

    entities = (message.entities or []) + (message.caption_entities or [])
    for e in entities:
        if e.type in ("mention", "url", "text_link"):
            return True

    return False


@router.message()
async def anti_spam_stub(message: types.Message, bot: Bot, **kwargs: Any):
    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    if not _has_mentions_or_links(message):
        return

    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(message.chat.id, me.id)

        can_delete = bool(getattr(member, "can_delete_messages", False))
        is_owner = member.status == "creator"
        is_admin = member.status == "administrator"

        if not (is_owner or (is_admin and can_delete)):
            log.warning(
                "No permission to delete messages in chat_id=%s (status=%s)",
                message.chat.id,
                getattr(member, "status", None),
            )
            return

        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        log.info("Deleted message %s in chat_id=%s", message.message_id, message.chat.id)

    except TelegramForbiddenError:
        log.warning("Forbidden: cannot delete in chat_id=%s", message.chat.id)
    except TelegramBadRequest as e:
        log.warning("BadRequest on delete in chat_id=%s: %s", message.chat.id, e)
    except Exception:
        log.exception("Unexpected error while trying to delete message")
