from typing import Optional
from pydantic import BaseModel


class AIHttpConfig(BaseModel):
    concurrency: int = 5
    timeout_s: float = 30.0
    max_connections: int = 50
    max_keepalive_connections: int = 20
    keepalive_expiry_s: float = 30.0


class AIConfig(BaseModel):
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.2
    spam_threshold: float = 0.3
    http: AIHttpConfig = AIHttpConfig()
