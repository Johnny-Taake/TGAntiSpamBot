from pydantic import BaseModel
from pathlib import Path


class DatabaseConfig(BaseModel):
    db_path: str = "database/database.db"

    echo: bool = False
    timeout: int = 30

    @property
    def url(self) -> str:
        return f"sqlite+aiosqlite:///{self.db_path}"

    def ensure_sqlite_file(self) -> Path:
        p = Path(self.db_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.touch()
        return p
