from typing import Literal

import logging
from pydantic import BaseModel

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class LoggingConfig(BaseModel):
    """Configuration for logging settings."""

    log_level: LogLevel = "DEBUG"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logs_dir: str = "logs"

    write_to_file: bool = False

    @property
    def log_level_enum(self) -> int:
        """Convert the log level string to the corresponding logging enum."""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return level_map[self.log_level]
