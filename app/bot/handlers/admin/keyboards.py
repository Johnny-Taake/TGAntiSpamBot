from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.db import Chat
from .pagination import paginate

MAX_TITLE = 34


def compact_title(title: str | None, max_len: int = MAX_TITLE) -> str:
    t = (title or "Unknown").strip()
    return (t[: max_len - 1] + "…") if len(t) > max_len else t


def build_chats_keyboard(
    chats: list[Chat],
    page: int = 0,
) -> InlineKeyboardMarkup:
    page_chats, total_pages = paginate(chats, page)

    rows: list[list[InlineKeyboardButton]] = []

    for chat in page_chats:
        status_icon = "✅" if chat.is_active else "⭕️"
        title = compact_title(chat.title)

        if chat.chat_link:
            right_button = InlineKeyboardButton(
                text="↗️",
                url=chat.chat_link,
            )
        else:
            right_button = InlineKeyboardButton(
                text="🔗",
                callback_data=f"gen_link_{chat.id}_{page}",
            )

        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{status_icon} {title}",
                    callback_data=f"toggle_chat_{chat.id}_{page}",
                ),
                right_button,
            ]
        )

    if total_pages > 1:
        nav = []
        if page > 0:
            nav.append(
                InlineKeyboardButton(text="⬅️", callback_data=f"page_chats_{page - 1}")
            )
        nav.append(
            InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop")
        )
        if page < total_pages - 1:
            nav.append(
                InlineKeyboardButton(text="➡️", callback_data=f"page_chats_{page + 1}")
            )
        rows.append(nav)

    rows.append(
        [
            InlineKeyboardButton(text="⚙️ Configure", callback_data="configure_chats"),
            InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh_chats"),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_chat_config_keyboard(chat: Chat, page: int = 0) -> InlineKeyboardMarkup:

    ai_status = "AI ✓" if chat.enable_ai_check else "AI ✗"
    ai_callback = f"toggle_ai_{chat.id}_{page}"

    mentions_status = "Mentions ✓" if chat.cleanup_mentions else "Mentions ✗"
    mentions_callback = f"toggle_mentions_{chat.id}_{page}"

    links_status = "Links ✓" if chat.cleanup_links else "Links ✗"
    links_callback = f"toggle_links_{chat.id}_{page}"

    back_callback = f"back_to_chats_{page}"

    keyboard = [
        [
            InlineKeyboardButton(text=ai_status, callback_data=ai_callback),
        ],
        [
            InlineKeyboardButton(text=mentions_status, callback_data=mentions_callback),
            InlineKeyboardButton(text=links_status, callback_data=links_callback),
        ],
        [
            InlineKeyboardButton(text="◀️ Back", callback_data=back_callback),
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
