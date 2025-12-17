import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram import Bot
from aiogram.types import User
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from app.bot.utils.message_actions import try_delete_message
from app.antispam.dto import MessageTask


@pytest.fixture
def bot():
    """Create a mock bot instance."""
    bot = AsyncMock(spec=Bot)
    bot.get_me.return_value = User(id=12345, is_bot=True, first_name="TestBot")
    return bot


@pytest.fixture
def spam_task():
    """Create a sample spam message task."""
    return MessageTask(
        telegram_chat_id=11111,
        telegram_message_id=22222,
        telegram_user_id=33333,
        text="spam message",
        entities=[],
    )


def create_chat_member(status: str, can_delete: bool = False):
    """Helper to create a mock chat member."""
    member = MagicMock()
    member.status = status
    member.can_delete_messages = can_delete
    return member


class TestTryDeleteMessage:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "status,can_delete",
        [
            ("creator", False),  # Owner always can delete
            ("administrator", True),  # Admin with permission
        ],
    )
    async def test_deletes_message_with_permissions(
        self, bot, spam_task, status, can_delete
    ):
        """Test message is deleted when bot has appropriate permissions."""
        bot.get_chat_member.return_value = create_chat_member(status, can_delete)

        await try_delete_message(bot, spam_task)

        bot.delete_message.assert_called_once_with(11111, 22222)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "status,can_delete",
        [
            ("member", False),  # Regular member
            ("administrator", False),  # Admin without permission
            ("restricted", False),  # Restricted user
        ],
    )
    async def test_skips_deletion_without_permissions(
        self, bot, spam_task, status, can_delete
    ):
        """Test message is not deleted when bot lacks permissions."""
        bot.get_chat_member.return_value = create_chat_member(status, can_delete)

        await try_delete_message(bot, spam_task)

        bot.delete_message.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "exception",
        [
            TelegramForbiddenError(message="Forbidden", method="deleteMessage"),
            TelegramBadRequest(message="Message not found", method="deleteMessage"),
            Exception("Unexpected error"),
        ],
    )
    async def test_handles_deletion_errors_gracefully(self, bot, spam_task, exception):
        """Test that deletion errors are caught and handled gracefully."""
        bot.get_chat_member.return_value = create_chat_member("administrator", True)
        bot.delete_message.side_effect = exception

        # Should not raise an exception
        await try_delete_message(bot, spam_task)

        bot.delete_message.assert_called_once_with(11111, 22222)

    @pytest.mark.asyncio
    async def test_handles_get_chat_member_error(self, bot, spam_task):
        """Test handling when checking bot permissions fails."""
        bot.get_chat_member.side_effect = TelegramBadRequest(
            message="Chat not found", method="getChatMember"
        )

        # Should not raise an exception
        await try_delete_message(bot, spam_task)

        # Should not attempt to delete if permission check fails
        bot.delete_message.assert_not_called()
