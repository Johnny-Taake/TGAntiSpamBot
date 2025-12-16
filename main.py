import uvicorn

from app.container import init_container
from config import config
from logger import setup_logging, get_logger


def main():
    setup_logging()
    init_container()

    log = get_logger(__name__)

    match config.bot.mode:
        case "polling":
            log.info("Running in polling mode")
            from app.bot.run_polling import run_polling

            run_polling()

        case "webhook":
            log.info("Running in webhook mode")
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
