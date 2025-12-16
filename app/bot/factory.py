from aiogram import Bot, Dispatcher

from app.bot.middleware.db_session import DbSessionMiddleware
from app.bot.handlers import router
from config import config


def create_bot_and_dispatcher() -> tuple[Bot, Dispatcher]:
    bot = Bot(token=config.bot.token)

    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware())
    dp.include_router(router)

    return bot, dp
