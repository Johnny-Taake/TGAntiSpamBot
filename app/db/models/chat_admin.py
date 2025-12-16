from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ChatAdmin(Base):
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), index=True, nullable=False
    )
    telegram_user_id: Mapped[int] = mapped_column(
        BigInteger, index=True, nullable=False
    )

    first_name: Mapped[str] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint("chat_id", "telegram_user_id", name="uq_chat_admin_chat_user"),
    )
