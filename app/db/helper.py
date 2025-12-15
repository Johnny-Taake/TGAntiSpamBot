from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker, AsyncSession
from sqlalchemy import event
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager

from logger import get_logger

log = get_logger(__name__)

class DataBaseHelper:
    def __init__(self, url: str, echo: bool = False, timeout: int = 30):
        if not url.startswith("sqlite"):
            raise NotImplementedError(f"Only SQLite supported. Got url={url!r}")

        self.engine: AsyncEngine = create_async_engine(
            url=url,
            echo=echo,
            connect_args={"timeout": timeout, "check_same_thread": False},
            poolclass=NullPool,
        )

        @event.listens_for(self.engine.sync_engine, "connect")
        def _set_sqlite_pragmas(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.close()

        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    # TODO: Use in lifespan
    async def dispose(self) -> None:
        await self.engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncSession:  # type: ignore
        async with self.session_factory() as session:
            try:
                yield session
            except Exception as e:
                log.exception(e)
                await session.rollback()
                raise
