from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.antispam.service import AntiSpamService
from app.monitoring import system_monitor


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
        # Increment request counter for each processed message/update
        system_monitor.increment_request_count()
        data["antispam"] = self.antispam_service
        try:
            return await handler(event, data)
        except Exception:
            system_monitor.increment_error_count()
            raise
