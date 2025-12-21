from aiogram import Bot
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.antispam.dto import MessageTask
from app.bot.utils import try_delete_message
from app.services import get_chat_by_telegram_id, get_or_create_user_state
from config import config
from logger import get_logger
from utils import ensure_utc_timezone, utc_now

from app.antispam.detectors.mentions import has_mentions
from app.antispam.detectors.links import has_links
from app.antispam.ai.moderator import AIModerator
from app.antispam.ai.notifier import RateLimitedNotifier

log = get_logger(__name__)


class MessageProcessor:
    """
    Handles the processing of individual messages for anti-spam checks.
    Separates the business logic from the service and queue handling.
    Orchestrates calls to specialized modules for different functionality.
    """

    def __init__(
        self,
        bot: Bot,
        ai_service=None,
        enable_ai_check: bool = True,
        cleanup_mentions: bool = True,
        cleanup_links: bool = True,
    ):
        self.bot = bot
        self.ai_service = ai_service
        self.enable_ai_check = enable_ai_check
        self.cleanup_mentions = cleanup_mentions
        self.cleanup_links = cleanup_links
        self._ai_moderator = AIModerator(ai_service)
        self._notifier = RateLimitedNotifier()

    async def process_message(self, session: AsyncSession, task: MessageTask) -> bool:
        """
        Process a single message task for spam detection.

        Args:
            session: Database session
            task: Message task to process

        Returns:
            True if message is valid (not spam), False if it was deleted
        """
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
                    enable_ai_check=config.bot.ai_enabled,
                    cleanup_mentions=True,
                    cleanup_links=True,
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
                await session.rollback()
                chat = await get_chat_by_telegram_id(session, task.telegram_chat_id)
                if chat is None:
                    log.error(
                        "Chat create race lost, but chat still missing: %s",
                        task.telegram_chat_id,
                    )
                    return True  # Consider message valid if chat creation fails

        if incoming_title and incoming_title != (chat.title or None):
            chat.title = incoming_title
            needs_commit = True

        if not chat.is_active:
            if needs_commit:
                await session.commit()
            return True

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
            log.debug(
                "User is trusted (time_ok=%s, msgs_ok=%s): chat_id=%s, user_id=%s, valid_messages=%s",
                time_ok, msgs_ok, chat.telegram_chat_id, task.telegram_user_id, user_state.valid_messages
            )
            return True

        # Use per-chat settings from the database instead of MessageProcessor constructor settings
        chat_enable_ai_check = chat.enable_ai_check
        chat_cleanup_mentions = chat.cleanup_mentions
        chat_cleanup_links = chat.cleanup_links

        # Check for mentions or links if enabled for this chat and delete message if found
        if (chat_cleanup_mentions and has_mentions(task)) or (chat_cleanup_links and has_links(task)):
            await try_delete_message(self.bot, task)
            if needs_commit:
                await session.commit()
            return False  # Message was deleted due to mentions/links

        # If global AI is disabled but the chat has AI enabled, log a warning
        if not config.bot.ai_enabled and chat_enable_ai_check:
            log.warning(
                "Chat %s has AI enabled but global AI is disabled. Using safe default (no AI).",
                chat.telegram_chat_id
            )
            chat_enable_ai_check = False

        if chat_enable_ai_check:
            success = await self._process_with_ai(
                session, task, user_state, needs_commit
            )
            return success
        else:
            needs_commit = True
            log.info(
                "Chat %s has AI disabled.",
                chat.telegram_chat_id
            )
            user_state.valid_messages += 1
            await session.commit()
            return True

    async def _process_with_ai(
        self,
        session: AsyncSession,
        task: MessageTask,
        user_state,
        needs_commit: bool,
    ) -> bool:
        """Process message using AI scoring."""
        from app.monitoring import system_monitor

        log.debug("Processing message with AI: %s", task)

        try:
            score = await self._ai_moderator.get_score(task)

            # Only increment AI requests counter if we actually made an AI call (not for empty text)
            if score is not None:
                system_monitor.increment_ai_requests_count()

            is_spam = self._ai_moderator.is_spam(score)

            if is_spam:
                # Increment spam blocked counter
                system_monitor.increment_spam_blocked_count()

                await try_delete_message(self.bot, task)
                if needs_commit:
                    await session.commit()
                return False  # Message was deleted

            # Not spam -> counts as valid
            old_valid_messages = user_state.valid_messages
            user_state.valid_messages += 1
            needs_commit = True

            # Check if user just became trusted (was not trusted before, but is now)
            now = utc_now()
            joined_at = ensure_utc_timezone(user_state.joined_at)
            was_trusted_before = (
                (now - joined_at).total_seconds() >= config.bot.min_seconds_in_chat and
                old_valid_messages >= config.bot.min_valid_messages
            )
            is_trusted_now = (
                (now - joined_at).total_seconds() >= config.bot.min_seconds_in_chat and
                user_state.valid_messages >= config.bot.min_valid_messages
            )
            newly_trusted = not was_trusted_before and is_trusted_now

            if newly_trusted:
                log.info(
                    "User became trusted: chat_id=%s, user_id=%s, valid_messages=%s",
                    task.telegram_chat_id, task.telegram_user_id, user_state.valid_messages
                )

        except Exception as e:
            log.warning(
                "AI moderation failed; treating as spam. chat_id=%s msg_id=%s err=%r",
                task.telegram_chat_id,
                task.telegram_message_id,
                e,
            )
            await try_delete_message(self.bot, task)
            # Send rate-limited notification to admin about AI service failure
            await self._notifier.notify(self.bot, str(e))
            if needs_commit:
                await session.commit()
            return False  # Message was deleted

        if needs_commit:
            await session.commit()

        return True  # Message is valid
