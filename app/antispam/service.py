import asyncio
from typing import Final, cast

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.antispam.dto import MessageTask
from app.bot.utils import try_delete_message
from app.services import get_chat_by_telegram_id, get_or_create_user_state
from config import config
from logger import get_logger
from utils import ensure_utc_timezone, utc_now

log = get_logger(__name__)

_SENTINEL: Final = object()


def detect_mentions_or_links(task: MessageTask) -> bool:
    text = (task.text or "").strip()
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
        self.queue: asyncio.Queue[MessageTask | object] = asyncio.Queue(
            maxsize=queue_size
        )
        self.workers = workers
        self._tasks: list[asyncio.Task[None]] = []
        self._started = False

    async def start(self, session_factory) -> None:
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
            "AntiSpamService started: workers=%s queue_size=%s",
            self.workers,
            self.queue.maxsize,
        )

    async def stop(self) -> None:
        if not self._started:
            return

        # Graceful stop: push one sentinel per worker
        for _ in self._tasks:
            await self.queue.put(_SENTINEL)

        # Wait workers to exit
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

    async def _worker_loop(self, idx: int, session_factory) -> None:
        while True:
            item = await self.queue.get()
            try:
                if item is _SENTINEL:
                    return

                task = cast(MessageTask, item)

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

    async def _process_one(self, session: AsyncSession, task: MessageTask) -> None:
        incoming_title = (task.chat_title or "").strip() or None
        needs_commit = False

        chat = await get_chat_by_telegram_id(session, task.telegram_chat_id)

        if chat is None:
            from app.db.models.chat import Chat

            try:
                chat = Chat(
                    telegram_chat_id=task.telegram_chat_id,
                    title=incoming_title,
                    is_active=False,
                )
                session.add(chat)
                await session.flush()
                needs_commit = True
                log.info(
                    "Created chat: telegram_chat_id=%s title=%r",
                    task.telegram_chat_id,
                    incoming_title,
                )
            except IntegrityError:
                # race: another worker inserted the same chat
                await session.rollback()
                chat = await get_chat_by_telegram_id(session, task.telegram_chat_id)
                if chat is None:
                    log.error(
                        "Chat create race lost, but chat still missing: %s",
                        task.telegram_chat_id,
                    )
                    return

        if incoming_title and incoming_title != (chat.title or None):
            chat.title = incoming_title
            needs_commit = True

        if not chat.is_active:
            if needs_commit:
                await session.commit()
            return

        user_state = await get_or_create_user_state(
            session,
            chat_id=chat.id,
            telegram_user_id=task.telegram_user_id,
        )

        now = utc_now()
        joined_at = ensure_utc_timezone(user_state.joined_at)

        time_ok = (now - joined_at).total_seconds() >= config.bot.min_seconds_in_chat
        msgs_ok = user_state.valid_messages >= config.bot.min_valid_messages
        trusted = time_ok and msgs_ok

        if trusted:
            if needs_commit:
                await session.commit()
            return

        if detect_mentions_or_links(task):
            await try_delete_message(self.bot, task)
            if needs_commit:
                await session.commit()
            return

        user_state.valid_messages += 1
        needs_commit = True

        if needs_commit:
            await session.commit()
