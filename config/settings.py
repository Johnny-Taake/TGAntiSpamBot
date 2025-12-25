from typing import Optional, Literal
import re
from urllib.parse import urlparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .config import Config

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="APP_", extra="ignore"
    )

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
    min_minutes_in_chat: Optional[int] = None
    min_valid_messages: Optional[int] = None

    # AntiSpam settings
    antispam_queue_size: Optional[int] = 20000
    antispam_workers: Optional[int] = 8
    fun_commands_enabled: Optional[bool] = None
    antispam_max_emojis: Optional[int] = None

    # AI settings
    ai_base_url: Optional[str] = None
    ai_api_key: Optional[str] = None
    ai_model: Optional[str] = None
    ai_enabled: Optional[bool] = None
    ai_temperature: Optional[float] = None
    ai_spam_threshold: Optional[float] = None

    http_concurrency: Optional[int] = None
    http_timeout_s: Optional[int] = None
    http_max_connections: Optional[int] = None
    http_max_keepalive_connections: Optional[int] = None
    http_keep_alive_expiry_s: Optional[int] = None

    @field_validator("bot_token")
    @classmethod
    def validate_bot_token(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r"^\d+:[a-zA-Z0-9_-]+$", v):
            raise ValueError("Invalid bot token format. Expected XXXX:YYYY")
        return v

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v

        parsed = urlparse(v)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Invalid webhook URL format")

        return v

    @field_validator(
        "db_timeout",
        "run_port",
        "main_admin_id",
        "min_minutes_in_chat",
        "min_valid_messages",
        "antispam_queue_size",
        "antispam_workers",
        "http_concurrency",
        "http_timeout_s",
        "http_max_connections",
        "http_max_keepalive_connections",
        "http_keep_alive_expiry_s",
    )
    @classmethod
    def validate_non_negative_ints(cls, v: Optional[int], info):
        if v is None:
            return v
        if v < 0:
            raise ValueError(f"{info.field_name} must be >= 0")
        return v

    @model_validator(mode="after")
    def validate_required_and_mode(self):
        # Required env vars
        if self.bot_token is None:
            raise ValueError("APP_BOT_TOKEN is required")

        if self.main_admin_id is None:
            raise ValueError("APP_MAIN_ADMIN_ID is required")

        # Conditional requirement for webhook mode
        mode = self.bot_mode or "polling"
        if mode == "webhook" and not self.webhook_url:
            raise ValueError(
                "APP_WEBHOOK_URL is required when APP_BOT_MODE=webhook"
            )

        return self

    def get_config(self) -> Config:
        config = Config()

        # Logging
        if self.log_level is not None:
            config.logging.log_level = self.log_level
        if self.write_to_file is not None:
            config.logging.write_to_file = self.write_to_file

        # Database
        if self.db_path is not None:
            config.database.db_path = self.db_path
        if self.db_echo is not None:
            config.database.echo = self.db_echo
        if self.db_timeout is not None:
            config.database.timeout = self.db_timeout

        # Bot core
        if self.run_port is not None:
            config.bot.port = self.run_port

        # These are guaranteed by model_validator
        config.bot.token = self.bot_token
        config.bot.main_admin_id = self.main_admin_id

        # Bot mode + webhook
        config.bot.mode = self.bot_mode or "polling"
        if self.webhook_url is not None:
            config.bot.webhook_url = self.webhook_url

        # Chat gating
        if self.min_minutes_in_chat is not None:
            config.bot.min_seconds_in_chat = self.min_minutes_in_chat * 60
        if self.min_valid_messages is not None:
            config.bot.min_valid_messages = self.min_valid_messages

        # AntiSpam
        if self.antispam_queue_size is not None:
            config.bot.antispam_queue_size = self.antispam_queue_size
        if self.antispam_workers is not None:
            config.bot.antispam_workers = self.antispam_workers
        if self.fun_commands_enabled is not None:
            config.bot.fun_commands_enabled = self.fun_commands_enabled
        if self.antispam_max_emojis is not None:
            config.bot.max_emojis = self.antispam_max_emojis

        # AI
        if self.ai_base_url is not None:
            config.ai.base_url = self.ai_base_url
        if self.ai_api_key is not None:
            config.ai.api_key = self.ai_api_key
        if self.ai_model is not None:
            config.ai.model = self.ai_model
        if self.ai_enabled is not None:
            config.bot.ai_enabled = self.ai_enabled
        if self.ai_temperature is not None:
            config.ai.temperature = self.ai_temperature
        if self.ai_spam_threshold is not None:
            config.ai.spam_threshold = self.ai_spam_threshold

        # HTTP (AI client)
        if self.http_concurrency is not None:
            config.ai.http.concurrency = self.http_concurrency
        if self.http_timeout_s is not None:
            config.ai.http.timeout_s = self.http_timeout_s
        if self.http_max_connections is not None:
            config.ai.http.max_connections = self.http_max_connections
        if self.http_max_keepalive_connections is not None:
            config.ai.http.max_keepalive_connections = (
                self.http_max_keepalive_connections
            )
        if self.http_keep_alive_expiry_s is not None:
            config.ai.http.keepalive_expiry_s = self.http_keep_alive_expiry_s

        return config


settings = Settings()
