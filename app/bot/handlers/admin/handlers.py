from aiogram import types, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.monitoring import system_monitor
from app.bot.filters import MainAdminFilter, PrivateChatFilter
from .constants import (
    HTML,
    MANAGED_CHATS_TEXT,
    NO_MANAGED_CHATS_TEXT,
)
from .keyboards import build_chats_keyboard
from .services import (
    fetch_group_chats,
    update_chat_titles,
)
from .renderers import render_chat_config
from .states import ChatWhitelistStates
from .utils import fetch_and_validate_chat
from logger import get_logger

log = get_logger(__name__)

router = Router()


@router.message(Command("chats"), PrivateChatFilter(), MainAdminFilter())
async def show_managed_chats(
    message: types.Message,
    session: AsyncSession,
) -> None:
    log.info("Admin %s requested list of managed chats", message.from_user.id)

    chats = await fetch_group_chats(session)
    if not chats:
        log.info("No managed chats found for admin %s", message.from_user.id)
        await message.reply(NO_MANAGED_CHATS_TEXT)
        return

    await update_chat_titles(session, message.bot, chats)
    await message.reply(
        MANAGED_CHATS_TEXT,
        reply_markup=build_chats_keyboard(chats, page=0),
    )
    log.info(
        "Sent list of %s managed chats to admin %s",
        len(chats),
        message.from_user.id,
    )


@router.message(Command("metrics"), PrivateChatFilter(), MainAdminFilter())
async def show_metrics(message: types.Message, session: AsyncSession) -> None:
    log.info("Admin %s requested system metrics", message.from_user.id)

    from app.container import get_antispam_service

    antispam_service = get_antispam_service()
    metrics = await system_monitor.get_system_metrics(
        db_session=session, antispam_service=antispam_service
    )
    report = system_monitor.format_metrics_for_admin(metrics)

    await message.reply(report, parse_mode=HTML)
    log.info("Sent system metrics to admin %s", message.from_user.id)


@router.message(
    ChatWhitelistStates.waiting_domains_to_remove,
    Command("cancel"),
)
@router.message(
    ChatWhitelistStates.waiting_domains_to_add,
    Command("cancel"),
)
async def cancel_whitelist_edit(
    message: types.Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    chat_id = data.get("chat_db_id")
    page = int(data.get("page", 0))

    await state.clear()
    await message.answer("Cancelled. Back to chat config -> /chats")

    if not chat_id:
        return

    chat = await fetch_and_validate_chat(
        session,
        callback_query=None,
        chat_id=chat_id,
    )
    if not chat:
        return

    await render_chat_config(message, chat, page=page)
