from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.sqlite import JSON

from app.db.base import Base


class Chat(Base):
    telegram_chat_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    chat_link: Mapped[str | None] = mapped_column(String(512), nullable=True)

    enable_ai_check: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    cleanup_mentions: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    cleanup_emojis: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    cleanup_links: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    allowed_link_domains: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    user_states = relationship(
        "UserState", back_populates="chat", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Chat id={self.id} tg={self.telegram_chat_id} active={self.is_active}>"  # noqa: E501
