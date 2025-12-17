import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.services.chat_registry import ChatRegistry, ChatCacheEntry
from app.db.models.chat import Chat


class TestChatCacheEntry:
    def test_cache_entry_creation(self):
        """Test that ChatCacheEntry is created correctly."""
        entry = ChatCacheEntry(last_seen_ts=12345.0, title="Test Chat")

        assert entry.last_seen_ts == 12345.0
        assert entry.title == "Test Chat"


class TestChatRegistry:
    def test_is_fresh_with_valid_entry(self):
        """Test that _is_fresh returns True for recent entries."""
        registry = ChatRegistry(ttl_seconds=3600)
        chat_id = 12345

        # Create an entry with recent timestamp
        registry._cache[chat_id] = ChatCacheEntry(
            last_seen_ts=1000000.0, title="Test Chat"
        )

        # Mock time.time to return a time within TTL
        with patch("app.services.chat_registry.time.time", return_value=1000001.0):
            assert registry._is_fresh(chat_id) is True

    def test_is_fresh_with_expired_entry(self):
        """Test that _is_fresh returns False for expired entries."""
        registry = ChatRegistry(ttl_seconds=3600)
        chat_id = 12345

        # Create an entry with old timestamp
        registry._cache[chat_id] = ChatCacheEntry(
            last_seen_ts=1000000.0, title="Test Chat"
        )

        # Mock time.time to return a time beyond TTL
        with patch("app.services.chat_registry.time.time", return_value=2000001.0):
            assert registry._is_fresh(chat_id) is False

    def test_touch_updates_cache(self):
        """Test that touch updates the cache entry."""
        registry = ChatRegistry(ttl_seconds=3600)
        chat_id = 12345
        title = "Updated Title"

        # Mock time.time to return a specific value
        with patch("app.services.chat_registry.time.time", return_value=123456.0):
            registry.touch(chat_id, title)

        assert chat_id in registry._cache
        assert registry._cache[chat_id].last_seen_ts == 123456.0
        assert registry._cache[chat_id].title == title

    @pytest.mark.asyncio
    async def test_ensure_chat_skips_fresh_cache(self):
        """Test that ensure_chat skips DB operations when cache is fresh."""
        registry = ChatRegistry(ttl_seconds=3600)
        session = AsyncMock(spec=AsyncSession)

        chat_id = 12345
        title = "Test Chat"

        # Add entry to cache to make it fresh
        registry._cache[chat_id] = ChatCacheEntry(last_seen_ts=1000000.0, title=title)

        # Mock time.time to return a time within TTL
        with patch("app.services.chat_registry.time.time", return_value=1000001.0):
            await registry.ensure_chat(
                session=session,
                telegram_chat_id=chat_id,
                title=title,
                default_is_active=False,
            )

        # Verify that no DB operations were performed
        session.execute.assert_not_called()
        session.add.assert_not_called()
        session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_chat_creates_new_chat(self):
        """Test that ensure_chat creates a new chat when it doesn't exist."""
        registry = ChatRegistry(ttl_seconds=3600)
        session = AsyncMock(spec=AsyncSession)

        chat_id = 12345
        title = "New Test Chat"

        # Mock the get_chat_by_telegram_id to return None (chat doesn't exist)
        with patch(
            "app.services.chat_registry.get_chat_by_telegram_id",
            AsyncMock(return_value=None),
        ):
            with patch(
                "app.services.chat_registry.time.time", side_effect=[500000.0, 500001.0]
            ):  # For cache check and touch
                await registry.ensure_chat(
                    session=session,
                    telegram_chat_id=chat_id,
                    title=title,
                    default_is_active=True,
                )

        # Verify that a new chat was created and added to session
        assert session.add.call_count == 1
        added_chat = session.add.call_args[0][0]
        assert isinstance(added_chat, Chat)
        assert added_chat.telegram_chat_id == chat_id
        assert added_chat.title == title
        assert added_chat.is_active is True  # default_is_active was True

        # Verify flush and commit were called
        session.flush.assert_called_once()
        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_chat_updates_existing_chat_title(self):
        """Test that ensure_chat updates title when changed."""
        registry = ChatRegistry(ttl_seconds=3600)
        session = AsyncMock(spec=AsyncSession)

        chat_id = 12345
        old_title = "Old Title"
        new_title = "New Title"

        # Create a mock chat
        mock_chat = MagicMock(spec=Chat)
        mock_chat.title = old_title

        # Mock the get_chat_by_telegram_id to return an existing chat
        with patch(
            "app.services.chat_registry.get_chat_by_telegram_id",
            AsyncMock(return_value=mock_chat),
        ):
            with patch(
                "app.services.chat_registry.time.time", side_effect=[500000.0, 500001.0]
            ):  # For cache check and touch
                await registry.ensure_chat(
                    session=session,
                    telegram_chat_id=chat_id,
                    title=new_title,
                    default_is_active=False,
                )

        # Verify that the chat title was updated
        assert mock_chat.title == new_title
        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_chat_handles_integrity_error(self):
        """Test that ensure_chat handles IntegrityError gracefully."""
        registry = ChatRegistry(ttl_seconds=3600)
        session = AsyncMock(spec=AsyncSession)

        chat_id = 12345
        title = "Test Chat"

        # Mock the get_chat_by_telegram_id to return None (chat doesn't exist)
        with patch(
            "app.services.chat_registry.get_chat_by_telegram_id",
            AsyncMock(return_value=None),
        ):
            # Make session.add raise an IntegrityError
            session.add.side_effect = IntegrityError("Duplicate entry", [], {})

            with patch("app.services.chat_registry.time.time", return_value=500000.0):
                await registry.ensure_chat(
                    session=session,
                    telegram_chat_id=chat_id,
                    title=title,
                    default_is_active=False,
                )

        # Verify that rollback was called
        session.rollback.assert_called_once()
        # Ensure cache was updated with the correct title
        assert chat_id in registry._cache
        assert registry._cache[chat_id].title == title
