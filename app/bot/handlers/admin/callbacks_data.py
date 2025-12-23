from aiogram.filters.callback_data import CallbackData


class ChatsCb(CallbackData, prefix="chats"):
    # action: list | toggle | gen_link | config | refresh | noop
    action: str
    page: int = 0


class ChatCb(CallbackData, prefix="chat"):
    # action: toggle | config
    action: str
    chat_id: int
    page: int = 0


class ChatFlagCb(CallbackData, prefix="chatflag"):
    # kind: ai | mentions | links
    kind: str
    chat_id: int
    page: int = 0
