from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Chat(Base):
    telegram_chat_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<Chat id={self.id} tg={self.telegram_chat_id} active={self.is_active}>"
