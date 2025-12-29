from contextlib import asynccontextmanager
from typing import AsyncGenerator

from aiogram.types import Update
from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse

from app.bot.factory import create_bot_and_dispatcher
from app.container import get_db
from config import config
from logger import get_logger
from app.monitoring import system_monitor
from app.bot.bootstrap import bootstrap_antispam_service
from app.bot.middleware.antispam import AntiSpamMiddleware

log = get_logger(__name__)

_antispam_service = None


def create_webhook_app() -> FastAPI:
    bot, dp = create_bot_and_dispatcher()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        global _antispam_service
        log.info("FastAPI lifespan startup: setting webhook...")

        db = get_db()

        try:
            _antispam_service = await bootstrap_antispam_service(db, bot)

            dp.update.middleware(AntiSpamMiddleware(_antispam_service))

            if not config.bot.webhook_url:
                raise RuntimeError(
                    "config.bot.webhook_url is empty but webhook mode is enabled"  # noqa: E501
                )

            # await bot.delete_webhook(drop_pending_updates=True)
            # log.info("Dropped pending updates, starting polling...")

            await bot.set_webhook(
                url=config.bot.webhook_url + config.bot.webhook_path,
                drop_pending_updates=True,
                allowed_updates=config.bot.allowed_updates,
            )

            log.info(
                "Webhook set: url=%s path=%s allowed_updates=%s",
                config.bot.webhook_url,
                config.bot.webhook_path,
                config.bot.allowed_updates,
            )

            yield
        except Exception as e:
            log.error(
                "Error in lifespan startup: %s Context: service=lifespan_startup",  # noqa: E501
                e,
                exc_info=True,
            )
            raise
        finally:
            log.info("FastAPI lifespan shutdown: removing webhook...")

            try:
                if _antispam_service:
                    await _antispam_service.stop()
            except Exception as e:
                log.error(
                    "Error stopping antispam: %s Context: service=antispam_stop",  # noqa: E501
                    e,
                    exc_info=True,
                )

            # Dispose of database resources
            try:
                await db.dispose()
            except Exception as e:
                log.error(
                    "Error disposing database: %s Context: service=database_dispose",  # noqa: E501
                    e,
                    exc_info=True,
                )

            try:
                await bot.delete_webhook()
            except Exception as e:
                log.error(
                    "Error deleting webhook: %s Context: service=webhook_delete",  # noqa: E501
                    e,
                    exc_info=True,
                )
            finally:
                try:
                    await bot.session.close()
                except Exception as e:
                    log.error(
                        "Error closing bot session: %s Context: service=bot_session_close",  # noqa: E501
                        e,
                        exc_info=True,
                    )

            log.info("FastAPI shutdown complete")

    app = FastAPI(
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
    )

    @app.post(config.bot.webhook_path)
    async def telegram_webhook(request: Request):
        try:
            data = await request.json()
            update = Update.model_validate(data)
            await dp.feed_webhook_update(bot, update)
            return {"ok": True}
        except Exception as e:
            system_monitor.increment_error_count()
            log.error(
                "Error in webhook handler: %s Context: service=webhook_handler, path=%s, request_method=%s",  # noqa: E501
                e,
                config.bot.webhook_path,
                request.method,
                exc_info=True,
            )
            try:
                raw_body = await request.body()
                log.warning(
                    "Webhook request body (on error): %s",
                    raw_body[:1000],
                )
            except Exception:
                pass

            return {"ok": False, "error": "Internal server error"}

    return app
