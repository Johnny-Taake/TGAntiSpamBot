from app.bot.factory import create_bot_and_dispatcher


def run_polling():
    bot, dp = create_bot_and_dispatcher()
    dp.run_polling(bot)
