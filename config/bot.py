from typing import Optional, Literal, List

from pydantic import BaseModel


class BotConfig(BaseModel):
    allowed_updates: List[str] = ["message", "callback_query"]

    token: Optional[str] = None
    mode: Literal["polling", "webhook"] = "polling"

    port: int = 8000

    webhook_url: Optional[str] = None
    webhook_path: str = "/webhook/bot/"

    main_admin_id: Optional[int] = None

    min_seconds_in_chat: int = 3600
    min_valid_messages: int = 5

    antispam_queue_size: int = 10000
    antispam_workers: int = 4

    fun_commands_enabled: bool = False

    ai_enabled: bool = False
