from dataclasses import dataclass
from typing import Optional

from config import config
from app.db import DataBaseHelper
from logger import get_logger

log = get_logger(__name__)


@dataclass
class AppContainer:
    cfg: object
    db: DataBaseHelper


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

    _container = AppContainer(cfg=config, db=db)
    return _container


def get_container() -> AppContainer:
    if _container is None:
        raise RuntimeError(
            "Container is not initialized. Call init_container() at startup."
        )
    return _container


def get_db() -> DataBaseHelper:
    return get_container().db
