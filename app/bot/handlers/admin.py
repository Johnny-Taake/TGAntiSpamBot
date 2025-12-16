from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.chat import Chat
from config import config
from logger import get_logger

log = get_logger(__name__)
router = Router()

MAX_TITLE = 14
PAGE_SIZE = 3


def compact_title(title: str | None, max_len: int = MAX_TITLE) -> str:
    t = (title or "Unknown").strip()
    return (t[: max_len - 1] + "…") if len(t) > max_len else t


def paginate(chats: list[Chat], page: int) -> tuple[list[Chat], int]:
    total_pages = max(1, (len(chats) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    return chats[start:end], total_pages


async def fetch_group_chats(session: AsyncSession) -> list[Chat]:
    result = await session.execute(select(Chat).where(Chat.telegram_chat_id < 0))
    return list(result.scalars().all())


async def update_chat_titles(session: AsyncSession, bot: Bot, chats: list[Chat]) -> bool:
    updated = False
    for chat in chats:
        if not chat.title or chat.title == f"Chat {chat.telegram_chat_id}":
            try:
                chat_obj = await bot.get_chat(chat.telegram_chat_id)
                new_title = getattr(chat_obj, "title", None)
                if new_title and chat.title != new_title:
                    chat.title = new_title
                    updated = True
            except Exception:
                continue

    if updated:
        await session.commit()

    return updated


def build_chats_keyboard(
    chats: list[Chat],
    page: int = 0,
) -> InlineKeyboardMarkup:
    page_chats, total_pages = paginate(chats, page)

    rows: list[list[InlineKeyboardButton]] = []

    for chat in page_chats:
        status_icon = "✅" if chat.is_active else "⭕️"
        title = compact_title(chat.title)

        left = InlineKeyboardButton(
            text=f"{status_icon} {title}",
            callback_data=f"toggle_chat_{chat.id}_{page}",
        )

        if chat.chat_link:
            right = InlineKeyboardButton(text="↗️", url=chat.chat_link)
        else:
            right = InlineKeyboardButton(text="🔗", callback_data=f"gen_link_{chat.id}_{page}")

        rows.append([left, right])

    if total_pages > 1:
        nav = []

        if page > 0:
            nav.append(
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"page_chats_{page - 1}",
                )
            )

        nav.append(
            InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}",
                callback_data="noop",
            )
        )

        if page < total_pages - 1:
            nav.append(
                InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"page_chats_{page + 1}",
                )
            )

        rows.append(nav)

    rows.append([InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh_chats")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def ensure_chat_link(session: AsyncSession, bot: Bot, chat: Chat) -> tuple[bool, str]:
    try:
        chat_obj = await bot.get_chat(chat.telegram_chat_id)
        username = getattr(chat_obj, "username", None)

        if username:
            link = f"https://t.me/{username}"
            if chat.chat_link != link:
                chat.chat_link = link
                await session.commit()
            return True, "Saved public link ↗️"

        invite = await bot.create_chat_invite_link(
            chat_id=chat.telegram_chat_id,
            name="Admin panel link",
            creates_join_request=False,
        )
        link = invite.invite_link
        chat.chat_link = link
        await session.commit()
        return True, "Invite link created ↗️"

    except Exception as e:
        log.warning("ensure_chat_link failed chat=%s err=%s", chat.telegram_chat_id, e)
        return False, "Can't create link (bot needs admin rights, or Telegram blocked it)."


@router.message(Command("chats"))
async def show_managed_chats(message: types.Message, session: AsyncSession):
    if message.from_user.id != config.bot.main_admin_id:
        await message.reply("❌ Only the main admin can manage chats.")
        return

    chats = await fetch_group_chats(session)

    if not chats:
        await message.reply("ℹ️ No groups/supergroups are being managed yet.")
        return

    await update_chat_titles(session, message.bot, chats)

    reply_markup = build_chats_keyboard(chats, page=0)
    await message.reply("📋 Managed chats:", reply_markup=reply_markup)


@router.callback_query(lambda c: c.data.startswith("toggle_chat_"))
async def toggle_chat_status(callback_query: types.CallbackQuery, session: AsyncSession):
    if callback_query.from_user.id != config.bot.main_admin_id:
        await callback_query.answer("❌ Only the main admin can manage chats.", show_alert=True)
        return

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

    await callback_query.answer("✅" if chat.is_active else "⭕️", show_alert=False)

    chats = await fetch_group_chats(session)
    try:
        await callback_query.message.edit_reply_markup(reply_markup=build_chats_keyboard(chats, page=page))
    except Exception:
        pass


@router.callback_query(lambda c: c.data.startswith("gen_link_"))
async def generate_chat_link(callback_query: types.CallbackQuery, session: AsyncSession):
    if callback_query.from_user.id != config.bot.main_admin_id:
        await callback_query.answer("❌ Only the main admin can manage chats.", show_alert=True)
        return

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
        await callback_query.message.edit_reply_markup(reply_markup=build_chats_keyboard(chats, page=page))
    except Exception:
        pass


@router.callback_query(lambda c: c.data.startswith("page_chats_"))
async def paginate_chats(callback_query: types.CallbackQuery, session: AsyncSession):
    if callback_query.from_user.id != config.bot.main_admin_id:
        await callback_query.answer("❌ Only the main admin can manage chats.", show_alert=True)
        return

    page = int(callback_query.data.split("_")[2])

    chats = await fetch_group_chats(session)
    await update_chat_titles(session, callback_query.bot, chats)

    await callback_query.message.edit_reply_markup(
        reply_markup=build_chats_keyboard(chats, page=page)
    )

    await callback_query.answer()


@router.callback_query(lambda c: c.data == "refresh_chats")
async def refresh_chats_list(callback_query: types.CallbackQuery, session: AsyncSession):
    if callback_query.from_user.id != config.bot.main_admin_id:
        await callback_query.answer("❌ Only the main admin can manage chats.", show_alert=True)
        return

    chats = await fetch_group_chats(session)

    if not chats:
        try:
            await callback_query.message.edit_text("ℹ️ No groups/supergroups are being managed yet.")
        except Exception:
            pass
        await callback_query.answer()
        return

    await update_chat_titles(session, callback_query.bot, chats)

    try:
        await callback_query.message.edit_reply_markup(reply_markup=build_chats_keyboard(chats, page=0))
    except Exception:
        await callback_query.answer("✅ Up to date!", show_alert=False)


@router.callback_query(lambda c: c.data == "noop")
async def noop(callback_query: types.CallbackQuery):
    await callback_query.answer()
