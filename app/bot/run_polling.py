import asyncio
from app.bot.factory import create_bot_and_dispatcher
from app.container import get_db, init_container
from app.antispam.service import AntiSpamService
from app.bot.middleware.antispam import AntiSpamMiddleware
from logger import get_logger

log = get_logger(__name__)


async def _run():
    init_container()

    db = get_db()
    bot, dp = create_bot_and_dispatcher()
    antispam = AntiSpamService(bot)

    try:
        log.info("Starting antispam service...")
        await antispam.start(db.session_factory)
        log.info("Antispam service started successfully")

        dp.update.middleware(AntiSpamMiddleware(antispam))
        log.info("Anti-spam middleware added to dispatcher")

        await bot.delete_webhook(drop_pending_updates=True)
        log.info("Webhook deleted, starting polling...")

        await dp.start_polling(bot)
    finally:
        log.info("Stopping antispam service...")
        await antispam.stop()

        # Dispose of database resources
        await db.dispose()

        log.info("Antispam service stopped")


def run_polling():
    asyncio.run(_run())
