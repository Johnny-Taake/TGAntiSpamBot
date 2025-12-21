import pytest
from unittest.mock import AsyncMock, Mock
from app.antispam.ai.moderator import AIModerator
from app.antispam.dto import MessageTask


class TestAIModerator:
    def test_init(self):
        """Test AIModerator initialization."""
        ai_service = Mock()
        moderator = AIModerator(ai_service)
        
        assert moderator.ai_service == ai_service

    @pytest.mark.asyncio
    async def test_get_score_returns_none_for_empty_text(self):
        """Test that get_score returns None when message text is empty."""
        ai_service = AsyncMock()
        moderator = AIModerator(ai_service)
        
        task = MessageTask(
            telegram_chat_id=123,
            telegram_message_id=456,
            telegram_user_id=789,
            text="",  # Empty text
            entities=[]
        )
        
        result = await moderator.get_score(task)
        
        assert result is None
        # Ensure AI service was not called for empty text
        ai_service.one_shot.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_score_calls_ai_service_and_processes_response(self):
        """Test that get_score calls AI service and processes the response."""
        ai_service = AsyncMock()
        # Mock AI service to return a response
        ai_service.one_shot.return_value = "The spam score is 0.75"
        
        moderator = AIModerator(ai_service)
        
        task = MessageTask(
            telegram_chat_id=123,
            telegram_message_id=456,
            telegram_user_id=789,
            text="Suspicious message content",
            entities=[]
        )
        
        result = await moderator.get_score(task)
        
        # Should return the extracted score
        assert result == 0.75
        # AI service should have been called
        ai_service.one_shot.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_score_handles_ai_service_exception(self):
        """Test that get_score handles exceptions from AI service."""
        ai_service = AsyncMock()
        ai_service.one_shot.side_effect = Exception("AI service unavailable")
        
        moderator = AIModerator(ai_service)
        
        task = MessageTask(
            telegram_chat_id=123,
            telegram_message_id=456,
            telegram_user_id=789,
            text="Normal message",
            entities=[]
        )
        
        with pytest.raises(Exception):
            await moderator.get_score(task)
    
    def test_is_spam_threshold_logic(self):
        """Test is_spam logic with different score values."""
        ai_service = Mock()
        moderator = AIModerator(ai_service)
        
        # Scores below threshold should not be considered spam
        assert moderator.is_spam(0.0) is False
        assert moderator.is_spam(0.1) is False
        assert moderator.is_spam(0.29) is False  # Just below default threshold
        
        # Score at threshold should be considered spam
        assert moderator.is_spam(0.3) is True  # At default threshold
        
        # Scores above threshold should be considered spam
        assert moderator.is_spam(0.4) is True
        assert moderator.is_spam(0.7) is True
        assert moderator.is_spam(1.0) is True
    
    def test_is_spam_handles_none_input(self):
        """Test is_spam handles None input."""
        ai_service = Mock()
        moderator = AIModerator(ai_service)

        # None scores should be treated as spam according to the actual implementation
        assert moderator.is_spam(None) is True
    
    @pytest.mark.asyncio
    async def test_get_score_with_special_characters_and_entities(self):
        """Test get_score with messages containing special characters and entities."""
        ai_service = AsyncMock()
        ai_service.one_shot.return_value = "Score: 0.45"
        
        moderator = AIModerator(ai_service)
        
        # Test with entities and special characters
        task = MessageTask(
            telegram_chat_id=123,
            telegram_message_id=456,
            telegram_user_id=789,
            text="Check @spam_account or visit https://suspicious-site.com",
            entities=[
                {"type": "mention", "offset": 6, "length": 12},
                {"type": "url", "offset": 25, "length": 27}
            ]
        )
        
        result = await moderator.get_score(task)
        
        assert result == 0.45
        ai_service.one_shot.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_score_empty_task(self):
        """Test get_score with minimal/empty task."""
        ai_service = AsyncMock()
        moderator = AIModerator(ai_service)
        
        task = MessageTask(
            telegram_chat_id=123,
            telegram_message_id=456,
            telegram_user_id=789,
            text=None,  # None text
            entities=None
        )
        
        result = await moderator.get_score(task)
        
        assert result is None
        ai_service.one_shot.assert_not_called()