import asyncio
import signal
import sys

from app.container import get_db
from config import config
from logger import get_logger
from app.bot.bootstrap import bootstrap_bot_for_polling

log = get_logger(__name__)


async def _run():
    db = get_db()
    bot, dp, antispam = await bootstrap_bot_for_polling(db)

    try:
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        log.info("Polling was cancelled")
    except KeyboardInterrupt:
        log.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        log.error(
            "Error in polling: %s Context: service=polling",
            e,
            exc_info=True,
        )
        raise
    finally:
        log.info("Stopping antispam service...")
        try:
            await antispam.stop()
        except Exception as e:
            log.error(
                "Error stopping antispam: %s Context: service=antispam_stop",
                e,
                exc_info=True,
            )

        try:
            await db.dispose()
        except Exception as e:
            log.error(
                "Error disposing database: %s Context: service=database_dispose",  # noqa: E501
                e,
                exc_info=True,
            )

        log.info("Antispam service stopped")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    log.info("Received signal %s, initiating graceful shutdown...", signum)
    sys.exit(0)


def run_polling():
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    log.info("Starting bot in polling mode...")
    log.info("Bot token configured: %s", "Yes" if config.bot.token else "No")
    log.info("Antispam queue size: %s", config.bot.antispam_queue_size)
    log.info("Antispam workers: %s", config.bot.antispam_workers)
    log.info("AI enabled: %s", config.bot.ai_enabled)

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        log.info("Application interrupted by user")
    except Exception as e:
        log.error("Error in main: %s Context: service=main", e, exc_info=True)
        sys.exit(1)
