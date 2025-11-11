"""Модель анализа сна"""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
import enum


class AnalysisStatus(str, enum.Enum):
    """Статусы анализа"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Analysis(Base):
    """Модель анализа сна"""
    
    __tablename__ = "analyses"
    
    # Основные поля
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    dream_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dreams.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # Один сон = один анализ
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Результат
    result: Mapped[str | None] = mapped_column(Text, nullable=True)  # nullable пока обрабатывается
    gpt_role: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Статус
    status: Mapped[str] = mapped_column(
        String(20),
        default=AnalysisStatus.PENDING.value,
        nullable=False,
        index=True
    )
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Связи
    dream: Mapped["Dream"] = relationship("Dream", back_populates="analysis")
    user: Mapped["User"] = relationship("User", back_populates="analyses")
    
    def __repr__(self) -> str:
        return f"<Analysis(id={self.id}, dream_id={self.dream_id}, status={self.status})>"

