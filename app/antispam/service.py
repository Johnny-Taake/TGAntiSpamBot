"""
Anti-Spam Service
"""

import asyncio
from typing import cast

from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker

from ai_client.service import AIService
from app.antispam.dto import MessageTask
from app.antispam.processors.message_processor import MessageProcessor
from app.antispam.utils import TTLSet, get_sentinel
from logger import get_logger


log = get_logger(__name__)

_SENTINEL = get_sentinel()


class AntiSpamService:
    """
    AI-based anti-spam service with queue-based processing.

    - No local rules (no mention/link checks).
    - Every non-admin message in active chats is sent to AI.
    - If score >= threshold -> delete message.
    - Else -> count as valid message.
    """

    def __init__(
        self,
        bot: Bot,
        ai_service: AIService,
        queue_size: int = 10_000,
        workers: int = 4,
        dedupe_ttl_s: int = 300,
        enable_ai_check: bool = True,
        cleanup_mentions: bool = True,
        cleanup_links: bool = True,
    ):
        # Only require AI service if AI check is enabled and AI is configured to be enabled
        if ai_service is None and enable_ai_check:
            from config import config

            if config.bot.ai_enabled:
                raise ValueError(
                    "ai_service is required when AI check is enabled in config"
                )
            else:
                # NOTE: If AI is disabled in config, it's okay for service to be None
                #   because the runtime check will prevent AI usage
                pass

        self.queue: asyncio.Queue[MessageTask | object] = asyncio.Queue(
            maxsize=queue_size
        )
        self.workers = workers

        self._tasks: list[asyncio.Task[None]] = []
        self._started = False

        # Configuration flags
        self.enable_ai_check = enable_ai_check
        self.cleanup_mentions = cleanup_mentions
        self.cleanup_links = cleanup_links

        # Store reference to config to check runtime AI enable/disable
        from config import config

        self.runtime_ai_enabled = config.bot.ai_enabled

        # Early dedupe for (chat_id, msg_id)
        self._seen = TTLSet(ttl_s=dedupe_ttl_s, max_size=2000)

        # Message processor for handling individual messages
        self._message_processor = MessageProcessor(
            bot,
            ai_service,
            enable_ai_check=enable_ai_check,
            cleanup_mentions=cleanup_mentions,
            cleanup_links=cleanup_links,
        )
        # Store reference for runtime AI enable/disable
        self._message_processor.runtime_ai_enabled = self.runtime_ai_enabled

    async def start(self, session_factory: async_sessionmaker):
        if self._started:
            return
        self._started = True

        self._tasks = [
            asyncio.create_task(
                self._worker_loop(i, session_factory), name=f"antispam-worker-{i}"
            )
            for i in range(self.workers)
        ]

        log.info(
            "AntiSpamService started (AI-only): queue_size=%s, workers=%s",
            self.queue.maxsize,
            self.workers,
        )

    async def stop(self):
        if not self._started:
            return

        # Graceful stop: push one sentinel per worker
        for _ in self._tasks:
            await self.queue.put(_SENTINEL)

        await asyncio.gather(*self._tasks, return_exceptions=True)

        self._tasks.clear()
        self._started = False
        log.info("AntiSpamService stopped")

    async def enqueue(self, task: MessageTask) -> None:
        try:
            self.queue.put_nowait(task)
        except asyncio.QueueFull:
            log.warning(
                "AntiSpam queue full -> waiting. chat_id=%s msg_id=%s user_id=%s",
                task.telegram_chat_id,
                task.telegram_message_id,
                task.telegram_user_id,
            )
            await self.queue.put(task)

    async def _worker_loop(self, idx: int, session_factory: async_sessionmaker):
        while True:
            item = await self.queue.get()
            try:
                if item is _SENTINEL:
                    return

                task = cast(MessageTask, item)

                key = (task.telegram_chat_id, task.telegram_message_id)
                if not self._seen.add_if_new(key):
                    log.debug(
                        "Duplicate task skipped: chat_id=%s msg_id=%s worker=%s",
                        task.telegram_chat_id,
                        task.telegram_message_id,
                        idx,
                    )
                    continue

                async with session_factory() as session:
                    try:
                        await self._message_processor.process_message(session, task)
                    except Exception:
                        log.exception(
                            "AntiSpam worker=%s failed: chat_id=%s msg_id=%s user_id=%s",
                            idx,
                            task.telegram_chat_id,
                            task.telegram_message_id,
                            task.telegram_user_id,
                        )
                        try:
                            await session.rollback()
                        except Exception:
                            log.exception("Rollback failed in worker=%s", idx)
            finally:
                self.queue.task_done()
