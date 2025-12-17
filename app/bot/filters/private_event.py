from aiogram.enums import ChatType
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery


class PrivateEventFilter(BaseFilter):
    """Allow only events that originate from a private chat."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        if isinstance(event, Message):
            return event.chat.type == ChatType.PRIVATE
        if isinstance(event, CallbackQuery) and event.message:
            return event.message.chat.type == ChatType.PRIVATE
        return False
