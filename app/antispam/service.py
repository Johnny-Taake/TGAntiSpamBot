from datetime import datetime, timezone

import asyncio
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.antispam.dto import MessageTask
from app.services import (
    get_or_create_user_state,
    get_chat_by_telegram_id,
)
from app.bot.utils import try_delete_message
from config import config
from logger import get_logger

log = get_logger(__name__)


def detect_mentions_or_links(task: MessageTask) -> bool:
    text = task.text or ""
    if not text:
        return False

    if "http://" in text or "https://" in text or "t.me/" in text or "www." in text:
        return True

    for e in task.entities or []:
        etype = e.get("type") if isinstance(e, dict) else getattr(e, "type", None)
        if etype in ("mention", "url", "text_link"):
            return True

    return False


class AntiSpamService:
    def __init__(self, bot: Bot, queue_size: int = 10_000, workers: int = 4):
        self.bot = bot
        self.queue: asyncio.Queue[MessageTask] = asyncio.Queue(maxsize=queue_size)
        self.workers = workers
        self._tasks: list[asyncio.Task] = []
        self._stop = asyncio.Event()

    async def start(self, session_factory):
        self._stop.clear()
        for i in range(self.workers):
            self._tasks.append(
                asyncio.create_task(self._worker_loop(i, session_factory))
            )

    async def stop(self):
        self._stop.set()
        for _ in self._tasks:
            await self.queue.put(None)
        for t in self._tasks:
            t.cancel()
        self._tasks.clear()


    async def enqueue(self, task: MessageTask):
        if self.queue.full():
            log.warning(
                "AntiSpam queue is full. Waiting for chat_id=%s msg_id=%s user_id=%s",
                task.telegram_chat_id,
                task.telegram_message_id,
                task.telegram_user_id,
            )
        await self.queue.put(task)


    async def _worker_loop(self, idx: int, session_factory):
        while not self._stop.is_set():
            task = await self.queue.get()
            if task is None:
                self.queue.task_done()
                break

            try:
                async with session_factory() as session:
                    try:
                        await self._process_one(session, task)
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

    async def _process_one(self, session: AsyncSession, task: MessageTask):
        log.debug(
            "process_one: chat_id=%s msg_id=%s user_id=%s",
            task.telegram_chat_id,
            task.telegram_message_id,
            task.telegram_user_id,
        )

        chat = await get_chat_by_telegram_id(session, task.telegram_chat_id)
        incoming_title = (task.chat_title or "").strip() or None

        log.debug("Chat lookup in antispam service for %s - exists: %s", task.telegram_chat_id, chat is not None)

        if not chat:
            from app.db.models.chat import Chat
            from sqlalchemy.exc import IntegrityError
            try:
                chat = Chat(
                    telegram_chat_id=task.telegram_chat_id,
                    title=incoming_title,
                    is_active=False,
                )
                session.add(chat)
                await session.commit()
                await session.refresh(chat)
                log.info("Antispam service created chat in DB: %s (%r)", task.telegram_chat_id, incoming_title)
            except IntegrityError:
                # Handle race condition where another worker created the same chat
                await session.rollback()
                chat = await get_chat_by_telegram_id(session, task.telegram_chat_id)
                if not chat:
                    log.error(f"Could not create or retrieve chat {task.telegram_chat_id}")
                    return
        else:
            if incoming_title and incoming_title != (chat.title or None):
                old_title = chat.title
                chat.title = incoming_title
                await session.commit()
                log.info("Antispam service updated chat title: %s - %r -> %r", task.telegram_chat_id, old_title, incoming_title)
            elif not chat.title and incoming_title:
                chat.title = incoming_title
                await session.commit()
                log.info("Antispam service set initial chat title: %s - %r", task.telegram_chat_id, incoming_title)

        if not chat:
            log.warning(f"No chat found for ID {task.telegram_chat_id}, skipping message")
            return

        if not chat.is_active:
            log.debug(
                "process_one: chat inactive telegram_chat_id=%s", task.telegram_chat_id
            )
            return

        user_state = await get_or_create_user_state(
            session,
            chat_id=chat.id,
            telegram_user_id=task.telegram_user_id,
        )

        log.debug("User state lookup result for chat %s, user %s - exists: %s",
                 chat.id, task.telegram_user_id, user_state.id if user_state else None)

        now = datetime.now(timezone.utc)

        joined_at = user_state.joined_at
        if joined_at.tzinfo is None:
            joined_at = joined_at.replace(tzinfo=timezone.utc)

        time_ok = (
            now - joined_at
        ).total_seconds() >= config.bot.min_seconds_in_chat
        msgs_ok = user_state.valid_messages >= config.bot.min_valid_messages
        trusted = time_ok and msgs_ok

        log.debug(
            "trust_check: chat_id=%s user_id=%s time_ok=%s msgs_ok=%s trusted=%s joined_at=%s valid_messages=%s",
            chat.id,
            task.telegram_user_id,
            time_ok,
            msgs_ok,
            trusted,
            user_state.joined_at,
            user_state.valid_messages,
        )

        if trusted:
            log.debug("Message trusted, skipping moderation: chat_id=%s msg_id=%s",
                     task.telegram_chat_id, task.telegram_message_id)
            return

        has_bad_content = detect_mentions_or_links(task)
        log.debug("content_check: chat_id=%s msg_id=%s has_bad_content=%s",
                 task.telegram_chat_id, task.telegram_message_id, has_bad_content)

        if has_bad_content:
            log.info("Deleting spam message: chat_id=%s msg_id=%s user_id=%s",
                    task.telegram_chat_id, task.telegram_message_id, task.telegram_user_id)
            await try_delete_message(self.bot, task)
            return

        user_state.valid_messages += 1
        await session.commit()
        log.debug(
            "valid_messages++ -> %s (chat_id=%s user_id=%s msg_id=%s)",
            user_state.valid_messages,
            chat.id,
            task.telegram_user_id,
            task.telegram_message_id,
        )
