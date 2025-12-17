from dataclasses import dataclass
from typing import Optional

from config import config
from app.db import DataBaseHelper
from app.services.chat_registry import ChatRegistry
from logger import get_logger

log = get_logger(__name__)


@dataclass
class AppContainer:
    cfg: object
    db: DataBaseHelper
    chat_registry: ChatRegistry


_container: Optional[AppContainer] = None


def init_container() -> AppContainer:
    global _container
    if _container is not None:
        return _container

    config.database.ensure_sqlite_file()

    db = DataBaseHelper(
        url=config.database.url,
        echo=config.database.echo,
        timeout=config.database.timeout,
    )

    log.info("Initializing database...")
    db.run_migrations()

    log.info("Initializing chat registry with TTL=%d seconds", 3600)
    chat_registry = ChatRegistry(ttl_seconds=3600)

    _container = AppContainer(cfg=config, db=db, chat_registry=chat_registry)
    log.info("Container initialized successfully with database and chat registry")
    return _container


def get_container() -> AppContainer:
    if _container is None:
        raise RuntimeError(
            "Container is not initialized. Call init_container() at startup."
        )
    return _container


def get_db() -> DataBaseHelper:
    return get_container().db


def get_chat_registry() -> ChatRegistry:
    registry = get_container().chat_registry
    log.debug("Chat registry accessed")
    return registry
