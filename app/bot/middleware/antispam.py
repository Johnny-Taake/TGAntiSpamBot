from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.antispam.service import AntiSpamService


class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self, antispam_service: AntiSpamService):
        super().__init__()
        self.antispam_service = antispam_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["antispam"] = self.antispam_service
        return await handler(event, data)
