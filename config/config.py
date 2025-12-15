from pydantic import BaseModel

from .logging import LoggingConfig
from .database import DatabaseConfig

class Config(BaseModel):

    logging: LoggingConfig = LoggingConfig()
    database: DatabaseConfig = DatabaseConfig()

    @property
    def LOG_LEVEL(self):
        return self.logging.log_level_enum

    @property
    def LOG_FORMAT(self) -> str:
        return self.logging.log_format
