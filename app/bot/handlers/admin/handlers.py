from aiogram import Router, types
from aiogram.filters import Command

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import Chat
from app.bot.filters import PrivateChatFilter, MainAdminFilter, PrivateEventFilter
from .services import (
    fetch_group_chats,
    update_chat_titles,
    ensure_chat_link,
)
from .keyboards import build_chats_keyboard

router = Router()


@router.message(Command("chats"), PrivateChatFilter(), MainAdminFilter())
async def show_managed_chats(message: types.Message, session: AsyncSession):
    chats = await fetch_group_chats(session)
    if not chats:
        await message.reply("ℹ️ No groups/supergroups are being managed yet.")
        return

    await update_chat_titles(session, message.bot, chats)
    await message.reply(
        "📋 Managed chats:",
        reply_markup=build_chats_keyboard(chats, page=0),
    )


@router.callback_query(PrivateEventFilter(), MainAdminFilter(), lambda c: c.data.startswith("toggle_chat_"))
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

    await callback_query.answer("✅ Activated" if chat.is_active else "⭕️ Deactivated", show_alert=False)

    chats = await fetch_group_chats(session)
    try:
        await callback_query.message.edit_reply_markup(
            reply_markup=build_chats_keyboard(chats, page=page)
        )
    except Exception:
        pass


@router.callback_query(PrivateEventFilter(), MainAdminFilter(), lambda c: c.data.startswith("gen_link_"))
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


@router.callback_query(PrivateEventFilter(), MainAdminFilter(), lambda c: c.data.startswith("page_chats_"))
async def paginate_chats(callback_query: types.CallbackQuery, session: AsyncSession):
    page = int(callback_query.data.split("_")[2])

    chats = await fetch_group_chats(session)
    await update_chat_titles(session, callback_query.bot, chats)

    await callback_query.message.edit_reply_markup(
        reply_markup=build_chats_keyboard(chats, page=page)
    )

    await callback_query.answer()


@router.callback_query(PrivateEventFilter(), MainAdminFilter(), lambda c: c.data == "refresh_chats")
async def refresh_chats_list(
    callback_query: types.CallbackQuery, session: AsyncSession
):
    chats = await fetch_group_chats(session)

    if not chats:
        try:
            await callback_query.message.edit_text(
                "ℹ️ No groups/supergroups are being managed yet."
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
        await callback_query.answer("✅ Up to date!", show_alert=False)


@router.callback_query(PrivateEventFilter(), MainAdminFilter(), lambda c: c.data == "noop")
async def noop(callback_query: types.CallbackQuery):
    await callback_query.answer()
