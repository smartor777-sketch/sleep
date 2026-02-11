"""Модель сообщения анализа (чат по снам)"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class MessageRole(str, enum.Enum):
    """Роли сообщений"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AnalysisMessage(Base):
    """Сообщение в чате анализа снов"""

    __tablename__ = "analysis_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    dream_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dreams.id", ondelete="CASCADE"),
        nullable=True
    )
    role: Mapped[str] = mapped_column(
        String(16),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    # Связи
    user: Mapped["User"] = relationship("User", back_populates="analysis_messages")
    dream: Mapped["Dream"] = relationship("Dream", back_populates="messages")

    __table_args__ = (
        Index("ix_analysis_messages_user_created", "user_id", "created_at"),
        Index("ix_analysis_messages_user_dream_created", "user_id", "dream_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AnalysisMessage(id={self.id}, role={self.role}, dream_id={self.dream_id})>"
