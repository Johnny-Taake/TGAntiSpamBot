from typing import Optional, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from .config import Config

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_")

    # Logging settings
    log_level: Optional[LogLevel] = None
    write_to_file: Optional[bool] = None

    db_path: Optional[str] = None
    db_echo: Optional[bool] = None
    db_timeout: Optional[int] = None

    def get_config(self) -> Config:
        config = Config()

        if self.log_level is not None:
            config.logging.log_level = self.log_level
        if self.write_to_file is not None:
            config.logging.write_to_file = self.write_to_file

        if self.db_path is not None:
            config.database.db_path = self.db_path
        if self.db_echo is not None:
            config.database.echo = self.db_echo
        if self.db_timeout is not None:
            config.database.timeout = self.db_timeout

        return config


settings = Settings()
