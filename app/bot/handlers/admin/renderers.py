from typing import Optional

from aiogram import Bot, types
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.admin.constants import HTML, MANAGED_CHATS_TEXT, NO_MANAGED_CHATS_TEXT, log
from app.bot.handlers.admin.keyboards import build_chat_config_keyboard, build_chats_keyboard
from app.bot.handlers.admin.services import fetch_group_chats, update_chat_titles
from app.db import Chat


async def edit_text(
    message: Optional[types.Message],
    text: str,
    *,
    parse_mode: Optional[str] = None,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
):
    if message is None:
        return
    try:
        await message.edit_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
        return
    except Exception:
        return


async def edit_reply_markup(
    message: Optional[types.Message],
    *,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
):
    if message is None:
        return False
    try:
        await message.edit_reply_markup(reply_markup=reply_markup)
        return
    except Exception:
        log.debug("edit_reply_markup failed (ignored)", exc_info=True)
        return


async def render_chat_config(
    message: Optional[types.Message],
    chat: Chat,
    page: int = 0,
):
    if message is None:
        return

    keyboard = build_chat_config_keyboard(chat, page)

    text = (
        f"🔧 <b>Configuring Chat: {chat.title or 'Unknown'}</b>\n"
        f"Chat ID: <code>{chat.telegram_chat_id}</code>\n\n"
        f"<b>AI Check:</b> {'Enabled' if chat.enable_ai_check else 'Disabled'}\n"
        f"<b>Cleanup Mentions:</b> {'Enabled' if chat.cleanup_mentions else 'Disabled'}\n"
        f"<b>Cleanup Links:</b> {'Enabled' if chat.cleanup_links else 'Disabled'}"
    )

    await edit_text(message, text, parse_mode=HTML, reply_markup=keyboard)


async def render_chats_list(
    message: Optional[types.Message],
    bot: Bot,
    session: AsyncSession,
    page: int,
    *,
    refresh_titles: bool = True,
):
    if message is None:
        return

    chats = await fetch_group_chats(session)
    if not chats:
        await edit_text(message, NO_MANAGED_CHATS_TEXT)
        return

    if refresh_titles:
        await update_chat_titles(session, bot, chats)

    await edit_text(
        message,
        MANAGED_CHATS_TEXT,
        reply_markup=build_chats_keyboard(chats, page=page),
    )


async def update_chats_list_markup(
    message: Optional[types.Message],
    bot: Bot,
    session: AsyncSession,
    page: int,
    *,
    refresh_titles: bool = True,
):
    if message is None:
        return

    chats = await fetch_group_chats(session)
    if not chats:
        # If chats list is empty, markup-only update doesn't make sense; show text.
        await edit_text(message, NO_MANAGED_CHATS_TEXT)
        return

    if refresh_titles:
        await update_chat_titles(session, bot, chats)

    await edit_reply_markup(
        message,
        reply_markup=build_chats_keyboard(chats, page=page),
    )
