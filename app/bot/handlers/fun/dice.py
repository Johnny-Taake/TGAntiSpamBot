from typing import Any

from aiogram import Router, types
from aiogram import Bot
from aiogram.filters import Command

from aiogram.enums.dice_emoji import DiceEmoji
from app.bot.filters import PrivateChatFilter


router = Router()


@router.message(Command("dice"), PrivateChatFilter())
async def dice(message: types.Message, bot: Bot, **kwargs: Any):
    # await bot.send_message(callback_query.from_user.id, "Your dice roll is...")
    _result = await bot.send_dice(message.chat.id, emoji=DiceEmoji.DICE)

    # import asyncio
    # await asyncio.sleep(4)
    # await bot.send_message(callback_query.from_user.id, f"Result: {_result.dice.value}")
