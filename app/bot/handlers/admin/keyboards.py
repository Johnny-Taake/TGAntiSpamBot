from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.db import Chat
from .pagination import paginate
from .callbacks_data import ChatCb, ChatsCb, ChatFlagCb, ChatWhitelistCb

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
            right_button = InlineKeyboardButton(text="↗️", url=chat.chat_link)
        else:
            right_button = InlineKeyboardButton(
                text="🔗",
                callback_data=ChatCb(
                    action="gen_link",
                    chat_id=chat.id,
                    page=page,
                ).pack(),
            )

        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{status_icon} {title}",
                    callback_data=ChatCb(
                        action="toggle",
                        chat_id=chat.id,
                        page=page,
                    ).pack(),
                ),
                right_button,
            ]
        )

    if total_pages > 1:
        nav: list[InlineKeyboardButton] = []
        if page > 0:
            nav.append(
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=ChatsCb(action="list", page=page - 1).pack(),
                )
            )

        nav.append(
            InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}",
                callback_data=ChatsCb(action="noop", page=page).pack(),
            )
        )

        if page < total_pages - 1:
            nav.append(
                InlineKeyboardButton(
                    text="➡️",
                    callback_data=ChatsCb(action="list", page=page + 1).pack(),
                )
            )
        rows.append(nav)

    rows.append(
        [
            InlineKeyboardButton(
                text="⚙️ Configure",
                callback_data=ChatsCb(action="config", page=page).pack(),
            ),
            InlineKeyboardButton(
                text="🔄 Refresh",
                callback_data=ChatsCb(action="refresh", page=0).pack(),
            ),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_chat_config_keyboard(
    chat: Chat,
    page: int = 0,
) -> InlineKeyboardMarkup:
    ai_status = "AI ✓" if chat.enable_ai_check else "AI ✗"
    mentions_status = "Mentions ✓" if chat.cleanup_mentions else "Mentions ✗"
    links_status = "Links ✓" if chat.cleanup_links else "Links ✗"
    emojis_status = "Emojis ✓" if chat.cleanup_emojis else "Emojis ✗"

    keyboard = [
        [
            InlineKeyboardButton(
                text=ai_status,
                callback_data=ChatFlagCb(
                    kind="ai",
                    chat_id=chat.id,
                    page=page,
                ).pack(),
            ),
            InlineKeyboardButton(
                text=emojis_status,
                callback_data=ChatFlagCb(
                    kind="emojis",
                    chat_id=chat.id,
                    page=page,
                ).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text=mentions_status,
                callback_data=ChatFlagCb(
                    kind="mentions",
                    chat_id=chat.id,
                    page=page,
                ).pack(),
            ),
            InlineKeyboardButton(
                text=links_status,
                callback_data=ChatFlagCb(
                    kind="links",
                    chat_id=chat.id,
                    page=page,
                ).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text=" ➕ Add domains",
                callback_data=ChatWhitelistCb(
                    action="add",
                    chat_id=chat.id,
                    page=page,
                ).pack(),
            ),
            InlineKeyboardButton(
                text=" ➖ Remove domains",
                callback_data=ChatWhitelistCb(
                    action="remove",
                    chat_id=chat.id,
                    page=page,
                ).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text="◀️ Back",
                callback_data=ChatsCb(action="list", page=page).pack(),
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
