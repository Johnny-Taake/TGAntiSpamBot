from aiogram import Router, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.filters import MainAdminFilter, PrivateEventFilter
from app.bot.handlers.admin.renderers import (
    edit_text,
    render_chat_config,
    render_chats_list,
    update_chats_list_markup,
)
from app.bot.handlers.admin.utils import (
    fetch_and_validate_chat,
    short_title,
    toggle_chat_flag,
)
from logger import get_logger
from .constants import HTML
from .services import ensure_chat_link, fetch_group_chats, update_chat_titles
from .callbacks_data import ChatCb, ChatFlagCb, ChatsCb

log = get_logger(__name__)

router = Router()


@router.callback_query(
    PrivateEventFilter(),
    MainAdminFilter(),
    ChatCb.filter(F.action == "toggle"),
)
async def toggle_chat_status(
    callback_query: types.CallbackQuery,
    callback_data: ChatCb,
    session: AsyncSession,
) -> None:
    chat = await fetch_and_validate_chat(session, callback_query, callback_data.chat_id)
    if not chat:
        return

    chat.is_active = not chat.is_active
    await session.commit()

    await callback_query.answer(
        "✅  Activated" if chat.is_active else "⭕️  Deactivated",
        show_alert=False,
    )

    await update_chats_list_markup(
        callback_query.message,
        callback_query.bot,
        session,
        callback_data.page,
        refresh_titles=False,
    )


@router.callback_query(
    PrivateEventFilter(),
    MainAdminFilter(),
    ChatCb.filter(F.action == "gen_link"),
)
async def generate_chat_link(
    callback_query: types.CallbackQuery,
    callback_data: ChatCb,
    session: AsyncSession,
) -> None:
    chat = await fetch_and_validate_chat(session, callback_query, callback_data.chat_id)
    if not chat:
        return

    ok, msg = await ensure_chat_link(session, callback_query.bot, chat)
    await callback_query.answer(msg, show_alert=not ok)

    await update_chats_list_markup(
        callback_query.message,
        callback_query.bot,
        session,
        callback_data.page,
        refresh_titles=False,
    )


@router.callback_query(
    PrivateEventFilter(),
    MainAdminFilter(),
    ChatsCb.filter(F.action == "list"),
)
async def paginate_chats(
    callback_query: types.CallbackQuery,
    callback_data: ChatsCb,
    session: AsyncSession,
) -> None:
    await render_chats_list(
        callback_query.message,
        callback_query.bot,
        session,
        callback_data.page,
        refresh_titles=False,
    )
    await callback_query.answer()


@router.callback_query(
    PrivateEventFilter(),
    MainAdminFilter(),
    ChatsCb.filter(F.action == "refresh"),
)
async def refresh_chats_list(
    callback_query: types.CallbackQuery,
    callback_data: ChatsCb,
    session: AsyncSession,
) -> None:
    await render_chats_list(
        callback_query.message, callback_query.bot, session, page=0, refresh_titles=True
    )
    await callback_query.answer("✅  Up to date!", show_alert=False)


@router.callback_query(
    PrivateEventFilter(),
    MainAdminFilter(),
    ChatsCb.filter(F.action == "noop"),
)
async def noop(
    callback_query: types.CallbackQuery,
    callback_data: ChatsCb,
) -> None:
    await callback_query.answer()


@router.callback_query(
    PrivateEventFilter(),
    MainAdminFilter(),
    ChatsCb.filter(F.action == "config"),
)
async def show_chats_for_configuration(
    callback_query: types.CallbackQuery,
    callback_data: ChatsCb,
    session: AsyncSession,
) -> None:
    chats = await fetch_group_chats(session)
    if not chats:
        await callback_query.answer("No chats to configure!", show_alert=True)
        return

    await update_chat_titles(session, callback_query.bot, chats)

    keyboard_rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=f"{short_title(chat)} ({'active' if chat.is_active else 'inactive'})",
                callback_data=ChatCb(action="config", chat_id=chat.id, page=0).pack(),
            )
        ]
        for chat in chats
    ]
    keyboard_rows.append(
        [InlineKeyboardButton(text="◀️ Back", callback_data=ChatsCb(action="list", page=0).pack())]
    )

    await edit_text(
        callback_query.message,
        "🔧 <b>Select a chat to configure:</b>",
        parse_mode=HTML,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_rows),
    )
    await callback_query.answer()


@router.callback_query(
    PrivateEventFilter(),
    MainAdminFilter(),
    ChatCb.filter(F.action == "config"),
)
async def show_chat_configuration(
    callback_query: types.CallbackQuery,
    callback_data: ChatCb,
    session: AsyncSession,
) -> None:
    chat = await fetch_and_validate_chat(session, callback_query, callback_data.chat_id)
    if not chat:
        return

    await render_chat_config(callback_query.message, chat, page=callback_data.page)
    await callback_query.answer()



@router.callback_query(
    PrivateEventFilter(),
    MainAdminFilter(),
    ChatFlagCb.filter(),
)
async def toggle_chat_flags(
    callback_query: types.CallbackQuery,
    callback_data: ChatFlagCb,
    session: AsyncSession,
) -> None:
    await toggle_chat_flag(
        callback_query,
        session,
        callback_data.kind,
        callback_data.chat_id,
        callback_data.page,
    )


@router.callback_query(
    PrivateEventFilter(),
    MainAdminFilter(),
    ChatsCb.filter(F.action == "list"),
)
async def show_chats_list(
    callback_query: types.CallbackQuery,
    callback_data: ChatsCb,
    session: AsyncSession,
) -> None:
    await render_chats_list(
        callback_query.message,
        callback_query.bot,
        session,
        callback_data.page,
        refresh_titles=False,
    )
    await callback_query.answer()
