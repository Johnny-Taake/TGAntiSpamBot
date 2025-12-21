from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import Chat
from app.bot.filters import PrivateChatFilter, MainAdminFilter, PrivateEventFilter
from app.monitoring import system_monitor
from config import config
from logger import get_logger
from app.services.chat_cached import cached_chat_service
from .services import (
    fetch_group_chats,
    update_chat_titles,
    ensure_chat_link,
)
from .keyboards import build_chats_keyboard, build_chat_config_keyboard

log = get_logger(__name__)

router = Router()


@router.message(Command("chats"), PrivateChatFilter(), MainAdminFilter())
async def show_managed_chats(message: types.Message, session: AsyncSession):
    log.info("Admin %s requested list of managed chats", message.from_user.id)
    chats = await fetch_group_chats(session)
    if not chats:
        log.info("No managed chats found for admin %s", message.from_user.id)
        await message.reply("ℹ️  No groups/supergroups are being managed yet.")
        return

    await update_chat_titles(session, message.bot, chats)
    await message.reply(
        "📋 Managed chats:\n==============================",
        reply_markup=build_chats_keyboard(chats, page=0),
    )
    log.info(
        "Sent list of %s managed chats to admin %s", len(chats), message.from_user.id
    )


@router.message(Command("metrics"), PrivateChatFilter(), MainAdminFilter())
async def show_metrics(message: types.Message, session: AsyncSession):
    log.info("Admin %s requested system metrics", message.from_user.id)
    from app.container import get_antispam_service

    antispam_service = get_antispam_service()

    metrics = await system_monitor.get_system_metrics(
        db_session=session, antispam_service=antispam_service
    )

    report = system_monitor.format_metrics_for_admin(metrics)
    await message.reply(report, parse_mode="HTML")
    log.info("Sent system metrics to admin %s", message.from_user.id)


@router.callback_query(
    PrivateEventFilter(), MainAdminFilter(), lambda c: c.data.startswith("toggle_chat_")
)
async def toggle_chat_status(
    callback_query: types.CallbackQuery, session: AsyncSession
):
    _, _, chat_id, page = callback_query.data.split("_")
    chat_id = int(chat_id)
    page = int(page)
    result = await session.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()

    if not chat or chat.telegram_chat_id >= 0:
        await callback_query.answer("Chat not found or not a group!", show_alert=True)
        return

    chat.is_active = not chat.is_active
    await session.commit()

    await callback_query.answer(
        "✅  Activated" if chat.is_active else "⭕️  Deactivated", show_alert=False
    )

    chats = await fetch_group_chats(session)
    try:
        await callback_query.message.edit_reply_markup(
            reply_markup=build_chats_keyboard(chats, page=page)
        )
    except Exception:
        pass


@router.callback_query(
    PrivateEventFilter(), MainAdminFilter(), lambda c: c.data.startswith("gen_link_")
)
async def generate_chat_link(
    callback_query: types.CallbackQuery, session: AsyncSession
):
    _, _, chat_id, page = callback_query.data.split("_")
    chat_id = int(chat_id)
    page = int(page)
    result = await session.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()

    if not chat or chat.telegram_chat_id >= 0:
        await callback_query.answer("Chat not found or not a group!", show_alert=True)
        return

    ok, msg = await ensure_chat_link(session, callback_query.bot, chat)
    await callback_query.answer(msg, show_alert=not ok)

    chats = await fetch_group_chats(session)
    try:
        await callback_query.message.edit_reply_markup(
            reply_markup=build_chats_keyboard(chats, page=page)
        )
    except Exception:
        pass


@router.callback_query(
    PrivateEventFilter(), MainAdminFilter(), lambda c: c.data.startswith("page_chats_")
)
async def paginate_chats(callback_query: types.CallbackQuery, session: AsyncSession):
    page = int(callback_query.data.split("_")[2])

    chats = await fetch_group_chats(session)
    await update_chat_titles(session, callback_query.bot, chats)

    await callback_query.message.edit_reply_markup(
        reply_markup=build_chats_keyboard(chats, page=page)
    )

    await callback_query.answer()


@router.callback_query(
    PrivateEventFilter(), MainAdminFilter(), lambda c: c.data == "refresh_chats"
)
async def refresh_chats_list(
    callback_query: types.CallbackQuery, session: AsyncSession
):
    chats = await fetch_group_chats(session)

    if not chats:
        try:
            await callback_query.message.edit_text(
                "ℹ️  No groups/supergroups are being managed yet."
            )
        except Exception:
            pass
        await callback_query.answer()
        return

    await update_chat_titles(session, callback_query.bot, chats)

    try:
        await callback_query.message.edit_reply_markup(
            reply_markup=build_chats_keyboard(chats, page=0)
        )
    except Exception:
        await callback_query.answer("✅  Up to date!", show_alert=False)


@router.callback_query(
    PrivateEventFilter(), MainAdminFilter(), lambda c: c.data == "noop"
)
async def noop(callback_query: types.CallbackQuery):
    await callback_query.answer()


@router.callback_query(
    PrivateEventFilter(), MainAdminFilter(), lambda c: c.data == "configure_chats"
)
async def show_chats_for_configuration(
    callback_query: types.CallbackQuery, session: AsyncSession
):
    """Show a list of chats for configuration."""
    chats = await fetch_group_chats(session)

    if not chats:
        await callback_query.answer("No chats to configure!", show_alert=True)
        return

    keyboard_rows = []
    for chat in chats:
        title = (chat.title or f"Chat {chat.telegram_chat_id}")[
            :20
        ]  # Limit title length
        keyboard_rows.append(
            [
                InlineKeyboardButton(
                    text=f"{title} ({'active' if chat.is_active else 'inactive'})",
                    callback_data=f"select_chat_config_{chat.id}",
                )
            ]
        )

    keyboard_rows.append(
        [InlineKeyboardButton(text="◀️ Back", callback_data="back_to_main_chats")]
    )

    await callback_query.message.edit_text(
        "🔧 <b>Select a chat to configure:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_rows),
    )
    await callback_query.answer()


@router.callback_query(
    PrivateEventFilter(),
    MainAdminFilter(),
    lambda c: c.data.startswith("select_chat_config_"),
)
async def show_chat_configuration(
    callback_query: types.CallbackQuery, session: AsyncSession
):
    """Show the configuration for a selected chat."""
    chat_id = int(callback_query.data.split("_")[3])

    result = await session.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()

    if not chat:
        await callback_query.answer("Chat not found!", show_alert=True)
        return

    keyboard = build_chat_config_keyboard(chat)

    await callback_query.message.edit_text(
        f"🔧 <b>Configuring Chat: {chat.title or 'Unknown'}</b>\n"
        f"Chat ID: <code>{chat.telegram_chat_id}</code>\n\n"
        f"<b>AI Check:</b> {'Enabled' if chat.enable_ai_check else 'Disabled'}\n"
        f"<b>Cleanup Mentions:</b> {'Enabled' if chat.cleanup_mentions else 'Disabled'}\n"
        f"<b>Cleanup Links:</b> {'Enabled' if chat.cleanup_links else 'Disabled'}",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    await callback_query.answer()


@router.callback_query(
    PrivateEventFilter(), MainAdminFilter(), lambda c: c.data.startswith("toggle_ai_")
)
async def toggle_ai_check(callback_query: types.CallbackQuery, session: AsyncSession):
    """Toggle AI check setting for a chat."""
    parts = callback_query.data.split("_")
    if len(parts) < 4:
        await callback_query.answer("Invalid data", show_alert=True)
        return

    _, _, chat_id, page = parts
    chat_id = int(chat_id)
    page = int(page)

    result = await session.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()

    if not chat:
        await callback_query.answer("Chat not found!", show_alert=True)
        return

    if not config.bot.ai_enabled and not chat.enable_ai_check:
        await callback_query.answer(
            "AI is globally disabled in the bot configuration. Enable it first!",
            show_alert=True,
        )
        return
    elif not config.bot.ai_enabled and chat.enable_ai_check:
        chat.enable_ai_check = not chat.enable_ai_check
        await session.commit()
        await callback_query.answer(
            f"AI check {'enabled' if chat.enable_ai_check else 'disabled'} for this chat",
            show_alert=False,
        )
    else:
        chat.enable_ai_check = not chat.enable_ai_check
        await session.commit()
        await callback_query.answer(
            f"AI check {'enabled' if chat.enable_ai_check else 'disabled'} for this chat",
            show_alert=False,
        )

    cached_chat_service.invalidate_chat(chat.telegram_chat_id)

    keyboard = build_chat_config_keyboard(chat, page)
    try:
        await callback_query.message.edit_text(
            f"🔧 <b>Configuring Chat: {chat.title or 'Unknown'}</b>\n"
            f"Chat ID: <code>{chat.telegram_chat_id}</code>\n\n"
            f"<b>AI Check:</b> {'Enabled' if chat.enable_ai_check else 'Disabled'}\n"
            f"<b>Cleanup Mentions:</b> {'Enabled' if chat.cleanup_mentions else 'Disabled'}\n"
            f"<b>Cleanup Links:</b> {'Enabled' if chat.cleanup_links else 'Disabled'}",
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    except Exception:
        pass


@router.callback_query(
    PrivateEventFilter(),
    MainAdminFilter(),
    lambda c: c.data.startswith("toggle_mentions_"),
)
async def toggle_mentions_cleanup(
    callback_query: types.CallbackQuery, session: AsyncSession
):
    """Toggle mentions cleanup setting for a chat."""
    parts = callback_query.data.split("_")
    if len(parts) < 4:
        await callback_query.answer("Invalid data", show_alert=True)
        return

    _, _, chat_id, page = parts
    chat_id = int(chat_id)
    page = int(page)

    result = await session.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()

    if not chat:
        await callback_query.answer("Chat not found!", show_alert=True)
        return

    chat.cleanup_mentions = not chat.cleanup_mentions
    await session.commit()
    await callback_query.answer(
        f"Mentions cleanup {'enabled' if chat.cleanup_mentions else 'disabled'} for this chat",
        show_alert=False,
    )

    cached_chat_service.invalidate_chat(chat.telegram_chat_id)

    keyboard = build_chat_config_keyboard(chat, page)
    try:
        await callback_query.message.edit_text(
            f"🔧 <b>Configuring Chat: {chat.title or 'Unknown'}</b>\n"
            f"Chat ID: <code>{chat.telegram_chat_id}</code>\n\n"
            f"<b>AI Check:</b> {'Enabled' if chat.enable_ai_check else 'Disabled'}\n"
            f"<b>Cleanup Mentions:</b> {'Enabled' if chat.cleanup_mentions else 'Disabled'}\n"
            f"<b>Cleanup Links:</b> {'Enabled' if chat.cleanup_links else 'Disabled'}",
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    except Exception:
        pass


@router.callback_query(
    PrivateEventFilter(),
    MainAdminFilter(),
    lambda c: c.data.startswith("toggle_links_"),
)
async def toggle_links_cleanup(
    callback_query: types.CallbackQuery, session: AsyncSession
):
    """Toggle links cleanup setting for a chat."""
    parts = callback_query.data.split("_")
    if len(parts) < 4:
        await callback_query.answer("Invalid data", show_alert=True)
        return

    _, _, chat_id, page = parts
    chat_id = int(chat_id)
    page = int(page)

    result = await session.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()

    if not chat:
        await callback_query.answer("Chat not found!", show_alert=True)
        return

    chat.cleanup_links = not chat.cleanup_links
    await session.commit()
    await callback_query.answer(
        f"Links cleanup {'enabled' if chat.cleanup_links else 'disabled'} for this chat",
        show_alert=False,
    )

    cached_chat_service.invalidate_chat(chat.telegram_chat_id)

    keyboard = build_chat_config_keyboard(chat, page)
    try:
        await callback_query.message.edit_text(
            f"🔧 <b>Configuring Chat: {chat.title or 'Unknown'}</b>\n"
            f"Chat ID: <code>{chat.telegram_chat_id}</code>\n\n"
            f"<b>AI Check:</b> {'Enabled' if chat.enable_ai_check else 'Disabled'}\n"
            f"<b>Cleanup Mentions:</b> {'Enabled' if chat.cleanup_mentions else 'Disabled'}\n"
            f"<b>Cleanup Links:</b> {'Enabled' if chat.cleanup_links else 'Disabled'}",
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    except Exception:
        pass


@router.callback_query(
    PrivateEventFilter(), MainAdminFilter(), lambda c: c.data == "back_to_main_chats"
)
async def back_to_main_chats_list(
    callback_query: types.CallbackQuery, session: AsyncSession
):
    """Go back to the main chats list."""
    chats = await fetch_group_chats(session)
    await update_chat_titles(session, callback_query.bot, chats)

    await callback_query.message.edit_text(
        "📋 Managed chats:\n==============================",
        reply_markup=build_chats_keyboard(chats, page=0),
    )
    await callback_query.answer()


@router.callback_query(
    PrivateEventFilter(),
    MainAdminFilter(),
    lambda c: c.data.startswith("back_to_chats_"),
)
async def back_to_chats_list(
    callback_query: types.CallbackQuery, session: AsyncSession
):
    """Go back to the chats list."""
    parts = callback_query.data.split("_")
    if len(parts) >= 4:
        page_str = parts[3]
        page = int(page_str)
    else:
        page = 0

    chats = await fetch_group_chats(session)
    await update_chat_titles(session, callback_query.bot, chats)

    await callback_query.message.edit_text(
        "📋 Managed chats:\n==============================",
        reply_markup=build_chats_keyboard(chats, page=page),
    )
    await callback_query.answer()
