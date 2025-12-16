from pydantic import BaseModel

from .logging import LoggingConfig
from .database import DatabaseConfig
from .bot import BotConfig

class Config(BaseModel):

    logging: LoggingConfig = LoggingConfig()
    database: DatabaseConfig = DatabaseConfig()
    bot: BotConfig = BotConfig()

    @property
    def LOG_LEVEL(self):
        return self.logging.log_level_enum

    @property
    def LOG_FORMAT(self) -> str:
        return self.logging.log_format
