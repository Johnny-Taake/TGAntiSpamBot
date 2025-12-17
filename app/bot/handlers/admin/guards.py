from aiogram import types
from aiogram.enums import ChatType

from config import config
from logger import get_logger

log = get_logger(__name__)


async def ensure_main_admin_private_chat(
    event: types.Message | types.CallbackQuery,
) -> bool:
    user = event.from_user

    if not user or user.id != config.bot.main_admin_id:
        log.warning("Access denied for user %s", user)
        return False

    if isinstance(event, types.CallbackQuery):
        if not event.message or not event.message.chat:
            log.warning("Access denied for callback query")
            return False
        chat = event.message.chat
    else:
        chat = event.chat

    log.debug("Chat type: %s", chat.type)

    if chat.type != ChatType.PRIVATE:
        log.warning("Access denied for non-private chat")
        return False

    return True
