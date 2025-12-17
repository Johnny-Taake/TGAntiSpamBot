from aiogram.enums import ChatType
from aiogram.filters import BaseFilter
from aiogram.types import Message


class PrivateChatFilter(BaseFilter):
    """Allow handler only in private chat."""

    async def __call__(self, message: Message) -> bool:
        return message.chat.type == ChatType.PRIVATE
