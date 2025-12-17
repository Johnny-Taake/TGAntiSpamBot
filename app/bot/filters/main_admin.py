from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from config import config


class MainAdminFilter(BaseFilter):
    """Allow only main admin."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return bool(event.from_user and event.from_user.id == config.bot.main_admin_id)
