from aiogram import Bot, Dispatcher

from app.bot.middleware.db_session import DbSessionMiddleware
from app.bot.middleware.chat_registry import ChatRegistryMiddleware
from app.bot.middleware.security import SecurityValidationMiddleware
from app.bot.handlers import router
from config import config
from logger import get_logger

log = get_logger(__name__)


def create_bot_and_dispatcher() -> tuple[Bot, Dispatcher]:
    log.info("Creating bot and dispatcher")
    bot = Bot(token=config.bot.token)

    dp = Dispatcher()
    log.debug("Adding middlewares to dispatcher")
    dp.update.middleware(SecurityValidationMiddleware())
    dp.update.middleware(DbSessionMiddleware())
    dp.update.middleware(ChatRegistryMiddleware())
    dp.include_router(router)
    log.info("Bot and dispatcher created successfully with all middlewares")

    return bot, dp
