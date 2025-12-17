from typing import Any

from aiogram import Router, types
from aiogram import Bot
from aiogram.filters import Command

from aiogram.enums.dice_emoji import DiceEmoji
from app.bot.filters import PrivateChatFilter


router = Router()


@router.message(Command("slot"), PrivateChatFilter())
async def slot(message: types.Message, bot: Bot, **kwargs: Any):
    await bot.send_dice(message.chat.id, emoji=DiceEmoji.SLOT_MACHINE)
