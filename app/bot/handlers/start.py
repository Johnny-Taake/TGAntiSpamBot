from aiogram import Router, types
from aiogram.filters import CommandStart

from app.bot.filters import PrivateChatFilter
from config import config

router = Router()


@router.message(CommandStart(), PrivateChatFilter())
async def start_command(message: types.Message):
    # Start building the welcome text
    welcome_text = (
        "<b>Welcome to TG AntiSpam Bot!</b>\n\n"
        "I'm designed to keep your groups safe from spam messages sent by bot users.\n\n"
        "<b>Available commands (private chats only):</b>\n"
        "• /start - Show this message\n"
        "• /about - Learn about the bot\n"
        "• /chats - Manage your groups (admin only)\n"
    )

    # Conditionally add fun commands based on configuration
    if config.bot.fun_commands_enabled:
        welcome_text += (
            "• /dice - Roll a dice (for fun)\n"
            "• /slot - Play slot machine (for fun)"
        )


    await message.answer(welcome_text, parse_mode="HTML")
