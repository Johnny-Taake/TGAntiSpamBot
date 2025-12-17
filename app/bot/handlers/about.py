from aiogram import Router, types
from aiogram.filters import Command

from app.bot.filters import PrivateChatFilter

router = Router()


@router.message(Command("about"), PrivateChatFilter())
async def about_command(message: types.Message):
    about_text = (
        "🛡️ <b>About TG AntiSpam Bot</b>\n\n"
        "This bot helps protect your Telegram groups from spam messages sent by bot users.\n\n"
        "<b>How it works:</b>\n"
        "• Monitors new messages in groups\n"
        "• Checks for suspicious content (links, mentions)\n"
        "• Tracks user behavior and trust level\n"
        "• Automatically removes spam messages\n\n"
        "<b>Trust System:</b>\n"
        "Users gain trust by staying in the group and sending valid messages.\n"
        "New users with links or mentions may have their messages deleted.\n\n"
        "<b>Features:</b>\n"
        "• Queue-based message processing\n"
        "• Configurable trust parameters\n"
        "• Admin handlers for group management\n"
        "• Database persistence\n"
        "• Support for both polling and webhook modes"
    )
    await message.answer(about_text, parse_mode="HTML")
