from contextlib import asynccontextmanager
from typing import AsyncGenerator

from aiogram.types import Update
from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse

from app.bot.factory import create_bot_and_dispatcher
from app.container import get_db, init_container
from app.antispam.service import AntiSpamService
from config import config
from logger import get_logger

log = get_logger(__name__)

_antispam_service: AntiSpamService = None


def create_webhook_app() -> FastAPI:
    init_container()

    bot, dp = create_bot_and_dispatcher()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        global _antispam_service
        log.info("FastAPI lifespan startup: setting webhook...")

        db = get_db()

        _antispam_service = AntiSpamService(bot)
        await _antispam_service.start(db.session_factory)

        from app.bot.middleware.antispam import AntiSpamMiddleware

        dp.update.middleware(AntiSpamMiddleware(_antispam_service))

        if not config.bot.webhook_url:
            raise RuntimeError(
                "config.bot.webhook_url is empty but webhook mode is enabled"
            )

        await bot.delete_webhook(drop_pending_updates=True)
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

        try:
            yield
        finally:
            log.info("FastAPI lifespan shutdown: removing webhook...")

            if _antispam_service:
                await _antispam_service.stop()

            try:
                await bot.delete_webhook()
            finally:
                await bot.session.close()

            log.info("FastAPI shutdown complete")

    app = FastAPI(
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
    )

    @app.post(config.bot.webhook_path)
    async def telegram_webhook(request: Request):
        data = await request.json()
        update = Update.model_validate(data)
        await dp.feed_webhook_update(bot, update)
        return {"ok": True}

    return app
