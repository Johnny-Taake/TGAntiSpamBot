from enum import Enum
from aiogram.filters.callback_data import CallbackData


class ChatsCb(CallbackData, prefix="chats"):
    class Action(str, Enum):
        LIST = "list"
        TOGGLE = "toggle"
        GEN_LINK = "gen_link"
        CONFIG = "config"
        REFRESH = "refresh"
        NOOP = "noop"

    action: Action
    page: int = 0


class ChatCb(CallbackData, prefix="chat"):
    class Action(str, Enum):
        TOGGLE = "toggle"
        CONFIG = "config"
        GEN_LINK = "gen_link"

    action: Action
    chat_id: int
    page: int = 0


class ChatFlagCb(CallbackData, prefix="chatflag"):
    class Kind(str, Enum):
        AI = "ai"
        MENTIONS = "mentions"
        LINKS = "links"
        EMOJIS = "emojis"

    kind: Kind
    chat_id: int
    page: int = 0


class ChatWhitelistCb(CallbackData, prefix="chatwl"):
    class Action(str, Enum):
        ADD = "add"
        REMOVE = "remove"

    action: Action
    chat_id: int
    page: int = 0
