from aiogram.fsm.state import StatesGroup, State


class ChatWhitelistStates(StatesGroup):
    waiting_domains_to_add = State()
    waiting_domains_to_remove = State()
