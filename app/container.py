from dataclasses import dataclass
from typing import Optional

from config import config
from ai_client.service import AIService
from app.db import DataBaseHelper
from app.services.chat_registry import ChatRegistry
from logger import get_logger

log = get_logger(__name__)


@dataclass
class AppContainer:
    cfg: object
    db: DataBaseHelper
    chat_registry: ChatRegistry
    ai_service: AIService


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

    # Initialize AI service only if it's enabled and configuration is provided
    ai_service = None
    required_ai_fields = [
        ('ai_enabled', config.bot.ai_enabled),
        ('base_url', config.ai.base_url),
        ('api_key', config.ai.api_key),
        ('model', config.ai.model),
    ]

    # Check which fields are missing for better observability
    missing_fields = [field for field, value in required_ai_fields if not value]

    if all(value for _, value in required_ai_fields):
        log.info("Initializing AI service with model: %s (AI enabled)", config.ai.model)
        ai_service = AIService()
    elif config.bot.ai_enabled:
        log.warning("AI service is enabled but configuration is incomplete. Missing: %s", missing_fields)
        ai_service = None
    else:
        log.info("AI service is disabled - skipping initialization")

    _container = AppContainer(
        cfg=config, db=db, chat_registry=chat_registry, ai_service=ai_service
    )
    log.info(
        "Container initialized successfully with database, chat registry, and AI service"
    )
    return _container


def set_antispam_service(antispam_service) -> None:
    """Set the antispam service after container initialization."""
    global _container
    if _container is not None:
        _container.antispam_service = antispam_service
    else:
        raise RuntimeError("Container must be initialized before setting antispam service")


def get_antispam_service():
    """Get the antispam service from the container."""
    global _container
    if _container is None:
        raise RuntimeError("Container is not initialized. Call init_container() at startup.")
    if not hasattr(_container, 'antispam_service'):
        return None
    return _container.antispam_service


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
