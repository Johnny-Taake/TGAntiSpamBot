from typing import Any

from aiogram import Router, types
from aiogram import Bot
from aiogram.filters import Command
from aiogram.enums import ChatType

from aiogram.enums.dice_emoji import DiceEmoji


router = Router()


@router.message(Command("dice"))
async def dice(message: types.Message, bot: Bot, **kwargs: Any):
    # await bot.send_message(callback_query.from_user.id, "Your dice roll is...")

    if message.chat.type != ChatType.PRIVATE:
        return

    _result = await bot.send_dice(message.chat.id, emoji=DiceEmoji.DICE)

    # import asyncio
    # await asyncio.sleep(4)
    # await bot.send_message(callback_query.from_user.id, f"Result: {_result.dice.value}")


@router.message(Command("slot"))
async def slot(message: types.Message, bot: Bot, **kwargs: Any):
    if message.chat.type != ChatType.PRIVATE:
        return

    await bot.send_dice(message.chat.id, emoji=DiceEmoji.SLOT_MACHINE)
