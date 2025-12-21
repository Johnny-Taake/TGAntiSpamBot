from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from app.security import sanitize_text
from logger import get_logger

log = get_logger(__name__)


class SecurityValidationMiddleware(BaseMiddleware):
    """
    Middleware to validate and sanitize incoming Telegram updates.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            # Validate and sanitize data based on event type
            if isinstance(event, Message):
                await self._validate_message(event)
            elif isinstance(event, CallbackQuery):
                await self._validate_callback_query(event)

            # Continue with the handler
            return await handler(event, data)

        except ValueError as e:
            log.warning(
                "Security validation failed for event %s: %s", type(event).__name__, e
            )
            # Send notification to admin about the security issue
            try:
                bot = data.get("bot")
                if bot:
                    from config import config
                    await bot.send_message(
                        chat_id=config.bot.main_admin_id,
                        text=f"🚨 Security validation failed for {type(event).__name__}: {e}"
                    )
            except Exception as notification_error:
                log.error("Failed to send security notification to admin: %s", notification_error)

            # Don't process the event if validation fails
            return None
        except Exception as e:
            log.error("Unexpected error in security validation: %s", e)
            # Continue with handler in case of unexpected errors to avoid blocking
            return await handler(event, data)

    async def _validate_message(self, message: Message) -> None:
        """Validate message data."""
        if message.text:
            message.text = sanitize_text(message.text)

        if message.caption:
            message.caption = sanitize_text(message.caption)

    async def _validate_callback_query(self, callback_query: CallbackQuery) -> None:
        """Validate callback query data."""
        if callback_query.data:
            callback_query.data = sanitize_text(callback_query.data)
