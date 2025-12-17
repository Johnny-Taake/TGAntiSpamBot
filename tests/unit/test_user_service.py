import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.services.user import get_or_create_user_state
from app.db.base import Base


@pytest_asyncio.fixture
async def async_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


class TestGetOrCreateUserState:
    @pytest.mark.asyncio
    async def test_creates_new_user_state(self, async_session):
        """Test creating a new user state when it doesn't exist."""
        user_state = await get_or_create_user_state(async_session, 123, 456)

        assert user_state.chat_id == 123
        assert user_state.telegram_user_id == 456
        assert user_state.id is not None

    @pytest.mark.asyncio
    async def test_returns_existing_user_state(self, async_session):
        """Test getting an existing user state."""
        # Create
        user_state1 = await get_or_create_user_state(async_session, 123, 456)
        await async_session.commit()
        original_id = user_state1.id

        # Get same one
        user_state2 = await get_or_create_user_state(async_session, 123, 456)

        assert user_state2.id == original_id
        assert user_state2.chat_id == 123
        assert user_state2.telegram_user_id == 456

    @pytest.mark.asyncio
    async def test_different_users_get_different_states(self, async_session):
        """Test that different users get separate state objects."""
        user_state1 = await get_or_create_user_state(async_session, 123, 456)
        user_state2 = await get_or_create_user_state(async_session, 123, 789)

        assert user_state1.id != user_state2.id
        assert user_state1.telegram_user_id == 456
        assert user_state2.telegram_user_id == 789
