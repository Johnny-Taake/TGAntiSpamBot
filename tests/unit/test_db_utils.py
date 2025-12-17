import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, Integer, String
from utils.db_utils import get_or_create


class Base(DeclarativeBase):
    pass


class SampleModel(Base):
    __tablename__ = "sample_model"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)


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


class TestGetOrCreate:
    @pytest.mark.asyncio
    async def test_get_existing_object(self, async_session):
        """Test retrieving an existing object."""
        obj1, created1 = await get_or_create(async_session, SampleModel, name="test")
        await async_session.commit()

        assert created1 is True
        assert obj1.name == "test"

        obj2, created2 = await get_or_create(async_session, SampleModel, name="test")

        assert created2 is False
        assert obj2.id == obj1.id
        assert obj2.name == "test"

    @pytest.mark.asyncio
    async def test_create_new_object(self, async_session):
        """Test creating a new object when it doesn't exist."""
        result, created = await get_or_create(
            async_session, SampleModel, name="new_test"
        )

        assert created is True
        assert result.name == "new_test"
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_multiple_unique_objects(self, async_session):
        """Test creating multiple objects with different unique keys."""
        obj1, created1 = await get_or_create(async_session, SampleModel, name="first")
        obj2, created2 = await get_or_create(async_session, SampleModel, name="second")

        assert created1 is True
        assert created2 is True
        assert obj1.id != obj2.id
        assert obj1.name == "first"
        assert obj2.name == "second"
