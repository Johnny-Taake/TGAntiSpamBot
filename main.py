from app.container import init_container
from config import config
from logger import setup_logging, get_logger


def main():
    setup_logging()

    log = get_logger(__name__)

    # Print startup information
    log.info("TGAntiSpamBot starting up...")
    log.info("Bot mode: %s", config.bot.mode)
    log.info("Bot token configured: %s", 'Yes' if config.bot.token else 'No')
    log.info("Main admin ID: %s", config.bot.main_admin_id)
    log.info("AI enabled: %s", config.bot.ai_enabled)
    if config.bot.ai_enabled:
        log.info("AI model: %s", config.ai.model)
        log.info("AI base URL: %s", config.ai.base_url)

    init_container()

    match config.bot.mode:
        case "polling":
            log.info("Starting in polling mode")
            from app.bot.run_polling import run_polling

            run_polling()

        case "webhook":
            log.info("Starting in webhook mode")
            log.info("Webhook URL: %s", config.bot.webhook_url)
            log.info("Webhook path: %s", config.bot.webhook_path)
            log.info("Port: %s", config.bot.port)

            import uvicorn

            from app.bot.run_webhook import create_webhook_app

            app = create_webhook_app()

            uvicorn.run(
                app,
                host="0.0.0.0",
                port=config.bot.port,
            )
        case _:
            raise RuntimeError(f"Unknown bot mode: {config.bot.mode}")


if __name__ == "__main__":
    main()
