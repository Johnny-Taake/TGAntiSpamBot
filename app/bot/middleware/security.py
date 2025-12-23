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
                await self._validate_message(event, data)
            elif isinstance(event, CallbackQuery):
                await self._validate_callback_query(event, data)

            # Continue with the handler
            return await handler(event, data)

        except ValueError as e:
            log.warning(
                "Security validation failed for event %s: %s", type(event).__name__, e  # noqa: E501
            )
            # Send notification to admin about the security issue
            try:
                bot = data.get("bot")
                if bot:
                    from config import config

                    await bot.send_message(
                        chat_id=config.bot.main_admin_id,
                        text=f"🚨 Security validation failed for {type(event).__name__}: {e}",  # noqa: E501
                    )
            except Exception as notification_error:
                log.error(
                    "Failed to send security notification to admin: %s",
                    notification_error,
                )

            # Don't process the event if validation fails
            return None
        except Exception as e:
            log.error("Unexpected error in security validation: %s", e)
            # Continue with handler in case of unexpected
            # errors to avoid blocking
            return await handler(event, data)

    async def _validate_message(self, message: Message, data: Dict[str, Any]):
        """Validate message data."""
        # Store sanitized text in middleware data
        if message.text:
            sanitized_text = sanitize_text(message.text)
            # Store in data dictionary for later use if needed
            data["sanitized_text"] = sanitized_text

        if message.caption:
            sanitized_caption = sanitize_text(message.caption)
            data["sanitized_caption"] = sanitized_caption

    async def _validate_callback_query(
        self, callback_query: CallbackQuery, data: Dict[str, Any]
    ) -> None:
        """Validate callback query data."""
        if callback_query.data:
            sanitized_data = sanitize_text(callback_query.data)
            # Store in data dictionary for later use if needed
            data["sanitized_callback_data"] = sanitized_data
