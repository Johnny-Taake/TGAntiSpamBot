__all__ = [
    "setup_logging",
    "get_logger",
]

import logging
import sys
from pathlib import Path

from config import config
from .colored_formatter import ColoredFormatter


def setup_logging():
    root_logger = logging.getLogger()

    for handler in root_logger.handlers[:]:
        try:
            handler.close()
        except Exception:
            pass
        root_logger.removeHandler(handler)

    root_logger.setLevel(config.LOG_LEVEL)

    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("aiogram.event").setLevel(logging.INFO)

    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(ColoredFormatter(config.LOG_FORMAT, use_color=True))
    root_logger.addHandler(console_handler)

    if config.logging.write_to_file:
        log_dir = Path(config.logging.logs_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(
            log_dir / "app.log",
            mode="w",
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
