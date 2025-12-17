import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.chat import get_chat_by_telegram_id
from app.db import Chat


class TestGetChatByTelegramId:
    @pytest.mark.asyncio
    async def test_returns_chat_when_found(self):
        """Test retrieving a chat that exists."""
        session = AsyncMock(spec=AsyncSession)
        mock_chat = MagicMock(spec=Chat)
        mock_chat.telegram_chat_id = 12345

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_chat
        session.execute.return_value = mock_result

        result = await get_chat_by_telegram_id(session, 12345)

        assert result == mock_chat
        session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        """Test retrieving a chat that doesn't exist."""
        session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = await get_chat_by_telegram_id(session, 99999)

        assert result is None
        session.execute.assert_called_once()
