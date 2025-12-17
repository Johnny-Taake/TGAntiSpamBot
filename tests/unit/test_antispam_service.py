import pytest
from unittest.mock import AsyncMock
from app.antispam.service import AntiSpamService, detect_mentions_or_links
from app.antispam.dto import MessageTask


class TestDetectMentionsOrLinks:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Visit https://example.com for more info", True),
            ("Check out http://example.com", True),
            ("Visit www.example.com for more info", True),
            ("Check out t.me/channel for updates", True),
            ("Hello, how are you?", False),
            ("", False),
            (None, False),
        ],
    )
    def test_detect_links_in_text(self, text, expected):
        """Test detecting various link patterns in message text."""
        task = MessageTask(
            telegram_chat_id=123,
            telegram_message_id=456,
            telegram_user_id=789,
            text=text,
            entities=[],
        )
        assert detect_mentions_or_links(task) is expected

    @pytest.mark.parametrize(
        "entity_type,expected",
        [
            ("mention", True),
            ("url", True),
            ("text_link", True),
            ("bold", False),
        ],
    )
    def test_detect_entities(self, entity_type, expected):
        """Test detecting spam-related entity types."""
        task = MessageTask(
            telegram_chat_id=123,
            telegram_message_id=456,
            telegram_user_id=789,
            text="Some text",
            entities=[{"type": entity_type}],
        )
        assert detect_mentions_or_links(task) is expected

    def test_detect_mixed_content(self):
        """Test message with both links and mentions."""
        task = MessageTask(
            telegram_chat_id=123,
            telegram_message_id=456,
            telegram_user_id=789,
            text="Check https://example.com and @username",
            entities=[{"type": "mention"}, {"type": "url"}],
        )
        assert detect_mentions_or_links(task) is True


class TestAntiSpamService:
    @pytest.mark.asyncio
    async def test_initialization_with_custom_params(self):
        """Test AntiSpamService initialization with custom parameters."""
        bot = AsyncMock()
        service = AntiSpamService(bot, queue_size=5000, workers=2)

        assert service.bot == bot
        assert service.queue.maxsize == 5000
        assert service.workers == 2
        assert service._started is False
        assert len(service._tasks) == 0

    @pytest.mark.asyncio
    async def test_initialization_with_defaults(self):
        """Test AntiSpamService initialization with default parameters."""
        bot = AsyncMock()
        service = AntiSpamService(bot)

        assert service.bot == bot
        assert service._started is False

    @pytest.mark.asyncio
    async def test_enqueue_adds_task_to_queue(self):
        """Test enqueuing a message task."""
        bot = AsyncMock()
        service = AntiSpamService(bot)

        task = MessageTask(
            telegram_chat_id=123,
            telegram_message_id=456,
            telegram_user_id=789,
            text="Test message",
            entities=[],
        )

        await service.enqueue(task)

        # Verify the task was added to the queue
        assert service.queue.qsize() == 1
        # Peek at the task without removing it
        queued_task = await service.queue.get()
        assert queued_task == task
        # Put it back for cleanup
        await service.queue.put(queued_task)

    @pytest.mark.asyncio
    async def test_enqueue_multiple_tasks(self):
        """Test enqueuing multiple tasks maintains order."""
        bot = AsyncMock()
        service = AntiSpamService(bot)

        tasks = [MessageTask(123, 456, 789, f"Message {i}", []) for i in range(3)]

        for task in tasks:
            await service.enqueue(task)

        assert service.queue.qsize() == 3
