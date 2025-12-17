from aiogram import Router, types
from aiogram.filters import CommandStart

from app.bot.filters import PrivateChatFilter

router = Router()


@router.message(CommandStart(), PrivateChatFilter())
async def start_command(message: types.Message):
    welcome_text = (
        "<b>Welcome to TG AntiSpam Bot!</b>\n\n"
        "I'm designed to keep your groups safe from spam messages sent by bot users.\n\n"
        "<b>Available commands (private chats only):</b>\n"
        "• /start - Show this message\n"
        "• /about - Learn about the bot\n"
        "• /chats - Manage your groups (admin only)\n"
        "• /dice - Roll a dice (for fun)\n"
        "• /slot - Play slot machine (for fun)\n\n"
        "For help managing the bot, contact the main administrator."
    )
    await message.answer(welcome_text, parse_mode="HTML")
