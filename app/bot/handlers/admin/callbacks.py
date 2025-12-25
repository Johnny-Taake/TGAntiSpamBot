from typing import Optional

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
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
from app.db import Chat
from logger import get_logger
from app.services.chat_cached import cached_chat_service
from .constants import HTML
from .services import ensure_chat_link, fetch_group_chats, update_chat_titles
from .callbacks_data import ChatCb, ChatFlagCb, ChatsCb, ChatWhitelistCb
from .states import ChatWhitelistStates
from .utils import add_allowed_link_domains, remove_allowed_link_domains


log = get_logger(__name__)

router = Router()


async def fetch_and_validate_chat_by_id(
    session: AsyncSession,
    chat_id: int,
) -> Optional[Chat]:
    chat = await session.get(Chat, chat_id)
    if not chat or chat.telegram_chat_id >= 0:
        return None
    return chat


@router.callback_query(
    PrivateEventFilter(),
    MainAdminFilter(),
    ChatCb.filter(F.action == ChatCb.Action.TOGGLE),
)
async def toggle_chat_status(
    callback_query: types.CallbackQuery,
    callback_data: ChatCb,
    session: AsyncSession,
) -> None:
    chat = await fetch_and_validate_chat(
        session,
        callback_query,
        callback_data.chat_id,
    )
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
    ChatCb.filter(F.action == ChatCb.Action.GEN_LINK),
)
async def generate_chat_link(
    callback_query: types.CallbackQuery,
    callback_data: ChatCb,
    session: AsyncSession,
) -> None:
    chat = await fetch_and_validate_chat(
        session,
        callback_query,
        callback_data.chat_id,
    )
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
    ChatsCb.filter(F.action == ChatsCb.Action.LIST),
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
    ChatsCb.filter(F.action == ChatsCb.Action.REFRESH),
)
async def refresh_chats_list(
    callback_query: types.CallbackQuery,
    callback_data: ChatsCb,
    session: AsyncSession,
) -> None:
    await render_chats_list(
        callback_query.message,
        callback_query.bot,
        session,
        page=0,
        refresh_titles=True,
    )
    await callback_query.answer("✅  Up to date!", show_alert=False)


@router.callback_query(
    PrivateEventFilter(),
    MainAdminFilter(),
    ChatsCb.filter(F.action == ChatsCb.Action.NOOP),
)
async def noop(
    callback_query: types.CallbackQuery,
    callback_data: ChatsCb,
) -> None:
    await callback_query.answer()


@router.callback_query(
    PrivateEventFilter(),
    MainAdminFilter(),
    ChatsCb.filter(F.action == ChatsCb.Action.CONFIG),
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
                text=f"{short_title(chat)} ({'active' if chat.is_active else 'inactive'})",  # noqa: E501
                callback_data=ChatCb(
                    action=ChatCb.Action.CONFIG,
                    chat_id=chat.id,
                    page=0,
                ).pack(),
            )
        ]
        for chat in chats
    ]
    keyboard_rows.append(
        [
            InlineKeyboardButton(
                text="◀️ Back",
                callback_data=ChatsCb(
                    action=ChatsCb.Action.LIST,
                    page=0,
                ).pack(),
            )
        ]
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
    ChatCb.filter(F.action == ChatCb.Action.CONFIG),
)
async def show_chat_configuration(
    callback_query: types.CallbackQuery,
    callback_data: ChatCb,
    session: AsyncSession,
) -> None:
    chat = await fetch_and_validate_chat(
        session,
        callback_query,
        callback_data.chat_id,
    )
    if not chat:
        return

    await render_chat_config(
        callback_query.message,
        chat,
        page=callback_data.page,
    )
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
    ChatsCb.filter(F.action == ChatsCb.Action.LIST),
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


@router.callback_query(ChatWhitelistCb.filter())
async def on_chat_whitelist_action(
    callback_query: types.CallbackQuery,
    callback_data: ChatWhitelistCb,
    session: AsyncSession,
    state: FSMContext,
):
    chat = await fetch_and_validate_chat(
        session,
        callback_query,
        callback_data.chat_id,
    )
    if not chat:
        return

    action = callback_data.action
    page = callback_data.page

    if action == ChatWhitelistCb.Action.ADD:
        await state.update_data(chat_db_id=chat.id, page=page)
        await state.set_state(ChatWhitelistStates.waiting_domains_to_add)
        await callback_query.answer()
        await callback_query.message.answer(
            "Send domains to ADD (space/comma separated).\n"
            "Example: repl.com github.com link.ru\n"
            "To cancel, send /cancel"
        )
        return

    if action == ChatWhitelistCb.Action.REMOVE:
        await state.update_data(chat_db_id=chat.id, page=page)
        await state.set_state(ChatWhitelistStates.waiting_domains_to_remove)
        await callback_query.answer()
        await callback_query.message.answer(
            "Send domains to REMOVE (space/comma separated).\n"
            "Example: github.com link.ru\n"
            "To cancel, send /cancel"
        )
        return

    await callback_query.answer("Unknown action", show_alert=True)


@router.message(ChatWhitelistStates.waiting_domains_to_add)
async def whitelist_add_domains(
    message: types.Message,
    session: AsyncSession,
    state: FSMContext,
):
    data = await state.get_data()
    chat_id = data.get("chat_db_id")

    if not chat_id:
        await state.clear()
        await message.answer("State error: chat not found.")
        return

    chat = await fetch_and_validate_chat(
        session,
        callback_query=None,
        chat_id=chat_id,
    )

    added = await add_allowed_link_domains(session, chat, message.text or "")
    cached_chat_service.invalidate_chat(chat.telegram_chat_id)

    await state.clear()

    if added:
        await message.answer("Added:\n" + "\n".join(f"• {d}" for d in added))
    else:
        await message.answer("Nothing added (maybe already present).")

    wl = chat.allowed_link_domains or []
    await message.answer(
        "Current whitelist:\n" +
        ("\n".join(f"• {d}" for d in wl) if wl else "empty") +
        "\n\n Back to chats config -> /chats"
    )


@router.message(ChatWhitelistStates.waiting_domains_to_remove)
async def whitelist_remove_domains(
    message: types.Message,
    session: AsyncSession,
    state: FSMContext,
):
    data = await state.get_data()
    chat_id = data.get("chat_db_id")

    if not chat_id:
        await state.clear()
        await message.answer("State error: chat not found.")
        return

    chat = await session.get(Chat, chat_id)
    if not chat or chat.telegram_chat_id >= 0:
        await state.clear()
        await message.answer("Chat not found or not a group!")
        return

    removed = await remove_allowed_link_domains(session, chat, message.text or "")  # noqa: E501
    cached_chat_service.invalidate_chat(chat.telegram_chat_id)

    await state.clear()

    if removed:
        await message.answer("Removed:\n" + "\n".join(f"• {d}" for d in removed))  # noqa: E501
    else:
        await message.answer("Nothing removed (not in whitelist).")

    wl = chat.allowed_link_domains or []
    await message.answer(
        "Current whitelist:\n" +
        ("\n".join(f"• {d}" for d in wl) if wl else "empty") +
        "\n\n Back to chats config -> /chats"
    )
