from typing import Optional, Literal

from pydantic import BaseModel

class BotConfig(BaseModel):
    token: Optional[str] = None
    mode: Literal["polling", "webhook"] = "polling"

    port: int = 8000

    webhook_url: Optional[str] = None
    webhook_path: str = "/webhook/bot/"
