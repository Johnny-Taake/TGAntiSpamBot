from sqlalchemy import BigInteger, ForeignKey, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone

from app.db.base import Base


class UserState(Base):
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), index=True, nullable=False
    )
    telegram_user_id: Mapped[int] = mapped_column(
        BigInteger, index=True, nullable=False
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    valid_messages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    chat = relationship("Chat", back_populates="user_states")

    __table_args__ = (
        UniqueConstraint("chat_id", "telegram_user_id", name="uq_user_state_chat_user"),
    )
