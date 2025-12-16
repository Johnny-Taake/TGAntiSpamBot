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

    # Database settings
    db_path: Optional[str] = None
    db_echo: Optional[bool] = None
    db_timeout: Optional[int] = None

    # Bot settings
    run_port: Optional[int] = None
    bot_token: Optional[str] = None
    bot_mode: Optional[Literal["polling", "webhook"]] = "polling"
    webhook_url: Optional[str] = None

    # Chat settings
    main_admin_id: Optional[int] = None
    min_minutes_in_chat: int = 3600
    min_valid_messages: int = 5

    # TODO: add usage by adding admins functionality
    register_code_ttl_minutes: int = 3600

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

        if self.run_port is not None:
            config.bot.port = self.run_port

        if self.bot_token is not None:
            config.bot.token = self.bot_token
        else:
            raise ValueError("BOT_TOKEN is not set")

        if self.bot_mode is not None:
            config.bot.mode = self.bot_mode

        if self.webhook_url is not None:
            config.bot.webhook_url = self.webhook_url
        elif config.bot.mode == "webhook":
            raise ValueError("WEBHOOK_URL is not set")

        if self.main_admin_id is not None:
            config.bot.main_admin_id = self.main_admin_id
        else:
            raise ValueError("MAIN_ADMIN_ID is not set")

        if self.min_minutes_in_chat is not None:
            config.bot.min_seconds_in_chat = self.min_minutes_in_chat * 60
        if self.min_valid_messages is not None:
            config.bot.min_valid_messages = self.min_valid_messages

        if self.register_code_ttl_minutes is not None:
            config.bot.register_code_ttl_seconds = self.register_code_ttl_minutes * 60

        return config


settings = Settings()
