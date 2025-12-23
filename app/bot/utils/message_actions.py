from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from logger import get_logger
from app.antispam.dto import MessageTask

log = get_logger(__name__)


async def try_delete_message(bot: Bot, task: MessageTask) -> None:
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(task.telegram_chat_id, me.id)

        can_delete = bool(getattr(member, "can_delete_messages", False))
        is_owner = getattr(member, "status", None) == "creator"
        is_admin = getattr(member, "status", None) == "administrator"

        if not (is_owner or (is_admin and can_delete)):
            log.warning(
                "No permission to delete messages in chat_id=%s (status=%s can_delete=%s)",  # noqa: E501
                task.telegram_chat_id,
                getattr(member, "status", None),
                can_delete,
            )
            return

        await bot.delete_message(
            task.telegram_chat_id,
            task.telegram_message_id
        )
        log.info(
            "Deleted message_id=%s chat_id=%s user_id=%s",
            task.telegram_message_id,
            task.telegram_chat_id,
            task.telegram_user_id,
        )

    except TelegramForbiddenError:
        log.warning(
            "Forbidden: cannot delete in chat_id=%s",
            task.telegram_chat_id
        )
    except TelegramBadRequest as e:
        log.warning(
            "BadRequest delete chat_id=%s msg_id=%s: %s",
            task.telegram_chat_id,
            task.telegram_message_id,
            e,
        )
    except Exception as e:
        log.exception("Unexpected error while trying to delete message: %s", e)
