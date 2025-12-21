"""
Rate-limited notification utilities
"""

import time
from aiogram import Bot

from config import config
from logger import get_logger

log = get_logger(__name__)


class RateLimitedNotifier:
    """
    Handles rate-limited admin notifications about AI service failures.
    """

    def __init__(self):
        self._last_ai_error_notification = 0

    async def notify(self, bot: Bot, error_msg: str):
        """
        Send rate-limited notification to admin about AI service failures.

        Args:
            bot: Bot instance to send the message
            error_msg: Error message to include in notification
        """
        # Check if we can send notification (rate limit: once per minute)
        current_time = time.time()
        if current_time - self._last_ai_error_notification < 60:
            return  # Skip notification

        try:
            await bot.send_message(
                chat_id=config.bot.main_admin_id,
                text=f"🚨 AI Service Error Alert!\n\nError: {error_msg}\n\nAI moderation is temporarily affected.",
            )
            self._last_ai_error_notification = current_time
            log.info("AI error notification sent to admin")
        except Exception as notification_error:
            log.error(
                "Failed to send AI error notification to admin: %s", notification_error
            )
