"""
Shared bootstrap module for bot initialization
"""

from typing import Tuple
from aiogram import Bot, Dispatcher

from app.antispam.service import AntiSpamService
from app.bot.middleware.antispam import AntiSpamMiddleware
from app.container import get_container, set_antispam_service
from app.bot.factory import create_bot_and_dispatcher
from config import config
from logger import get_logger

log = get_logger(__name__)


async def bootstrap_bot_for_polling(
        db
) -> Tuple[Bot, Dispatcher, AntiSpamService]:
    """
    Bootstrap function for polling mode that handles:
    - Bot creation
    - Dispatcher creation
    - AntiSpamService creation & startup
    - Middleware registration
    - Container wiring

    Args:
        db: Database instance containing session factory

    Returns:
        Tuple of (bot, dispatcher, antispam_service)
    """
    bot, dp = create_bot_and_dispatcher()

    container = get_container()

    antispam = AntiSpamService(
        bot,
        ai_service=container.ai_service,
        queue_size=config.bot.antispam_queue_size,
        workers=config.bot.antispam_workers,
    )

    await antispam.start(db.session_factory)
    set_antispam_service(antispam)

    dp.update.middleware(AntiSpamMiddleware(antispam))

    log.info("Bot bootstrap completed")

    return bot, dp, antispam


async def bootstrap_antispam_service(db, bot: Bot) -> AntiSpamService:
    """
    Bootstrap function for antispam service only
    (for webhook mode where bot/dispatcher are created separately).

    Args:
        db: Database instance containing session factory
        bot: Bot instance to use for the antispam service

    Returns:
        AntiSpamService instance
    """
    container = get_container()

    antispam = AntiSpamService(
        bot,
        ai_service=container.ai_service,
        queue_size=config.bot.antispam_queue_size,
        workers=config.bot.antispam_workers,
    )

    await antispam.start(db.session_factory)
    set_antispam_service(antispam)

    log.info("Antispam service bootstrap completed")

    return antispam
