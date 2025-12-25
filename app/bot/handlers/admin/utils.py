from typing import Optional

from aiogram import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.admin.renderers import render_chat_config
from app.db import Chat
from app.services.chat_cached import cached_chat_service
from config import config
from utils import parse_domains
from logger import get_logger

log = get_logger(__name__)


def short_title(chat: Chat, max_len: int = 20) -> str:
    title = (chat.title or f"Chat {chat.telegram_chat_id}").strip()
    if len(title) <= max_len:
        return title
    return title[: max_len - 1] + "…"


async def fetch_and_validate_chat(
    session: AsyncSession,
    callback_query: Optional[types.CallbackQuery],
    chat_id: int,
) -> Optional[Chat]:
    result = await session.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()

    if not chat or chat.telegram_chat_id >= 0:
        if callback_query:
            await callback_query.answer(
                "Chat not found or not a group!",
                show_alert=True,
            )
        else:
            log.error("Chat not found or not a group: %s", chat_id)
        return None

    return chat


TOGGLEABLE_FIELDS: dict[str, tuple[str, str]] = {
    "ai": ("enable_ai_check", "AI check"),
    "mentions": ("cleanup_mentions", "Mentions cleanup"),
    "links": ("cleanup_links", "Links cleanup"),
    "emojis": ("cleanup_emojis", "Emojis cleanup"),
}


async def toggle_chat_flag(
    callback_query: types.CallbackQuery,
    session: AsyncSession,
    flag_type: str,
    chat_id: int,
    page: int,
):
    if flag_type not in TOGGLEABLE_FIELDS:
        await callback_query.answer("Invalid toggle type", show_alert=True)
        return

    field_name, display_name = TOGGLEABLE_FIELDS[flag_type]

    chat = await fetch_and_validate_chat(session, callback_query, chat_id)
    if not chat:
        return

    current_value = bool(getattr(chat, field_name))
    target_value = not current_value

    # AI specific guard: don't allow enabling per-chat
    # when globally disabled
    if flag_type == "ai" and target_value and not config.bot.ai_enabled:
        await callback_query.answer(
            "AI is globally disabled in the bot configuration. Enable it first!",  # noqa: E501
            show_alert=True,
        )
        return

    setattr(chat, field_name, target_value)
    await session.commit()

    await callback_query.answer(
        f"{display_name} {'enabled' if target_value else 'disabled'} for this chat",  # noqa: E501
        show_alert=False,
    )

    cached_chat_service.invalidate_chat(chat.telegram_chat_id)

    await render_chat_config(callback_query.message, chat, page)


async def add_allowed_link_domains(
    session: AsyncSession,
    chat: Chat,
    raw: str,
) -> list[str]:
    """
    Add domains to allowlist.
    raw: "repl.com link.com link.ru github.com"
    """
    incoming = parse_domains(raw)
    current = set(chat.allowed_link_domains or [])

    added: list[str] = []
    for d in incoming:
        if d not in current:
            current.add(d)
            added.append(d)

    if added:
        chat.allowed_link_domains = sorted(current)
        session.add(chat)
        await session.commit()
        log.debug(
            "Added allowed domains to chat %s: %s",
            chat.telegram_chat_id,
            added,
        )

    return added


async def remove_allowed_link_domains(
    session: AsyncSession,
    chat: Chat,
    raw: str,
) -> list[str]:
    """
    Remove domains from allowlist.
    raw: "repl.com link.com link.ru github.com"
    """
    to_remove = set(parse_domains(raw))
    current = set(chat.allowed_link_domains or [])

    removed = sorted(current.intersection(to_remove))
    if removed:
        current.difference_update(to_remove)
        chat.allowed_link_domains = sorted(current)
        session.add(chat)
        await session.commit()
        log.debug(
            "Removed allowed domains from chat %s: %s",
            chat.telegram_chat_id,
            removed,
        )

    return removed
