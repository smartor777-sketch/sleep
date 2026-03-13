"""Модель сна"""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Dream(Base):
    """Модель сна"""
    
    __tablename__ = "dreams"
    
    # Основные поля
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Содержимое
    title: Mapped[str | None] = mapped_column(String(64), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    emoji: Mapped[str] = mapped_column(String(10), default="", nullable=False)
    comment: Mapped[str] = mapped_column(String(256), default="", nullable=False)
    gradient_color_1: Mapped[str | None] = mapped_column(String(7), nullable=True)
    gradient_color_2: Mapped[str | None] = mapped_column(String(7), nullable=True)
    # P2 scaffold for semantic search storage. Real vector index can replace this.
    embedding_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    embedding_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Временные метки
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Связи
    user: Mapped["User"] = relationship("User", back_populates="dreams")
    analysis: Mapped["Analysis"] = relationship(
        "Analysis",
        back_populates="dream",
        uselist=False,
        cascade="all, delete-orphan"
    )
    chunks: Mapped[list["DreamChunk"]] = relationship(
        "DreamChunk",
        back_populates="dream",
        cascade="all, delete-orphan",
        order_by="DreamChunk.chunk_index",
    )
    symbols: Mapped[list["DreamSymbol"]] = relationship(
        "DreamSymbol",
        back_populates="dream",
        cascade="all, delete-orphan",
    )
    symbol_entities: Mapped[list["DreamSymbolEntity"]] = relationship(
        "DreamSymbolEntity",
        back_populates="dream",
        cascade="all, delete-orphan",
    )
    dream_archetypes: Mapped[list["DreamArchetype"]] = relationship(
        "DreamArchetype",
        back_populates="dream",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list["AnalysisMessage"]] = relationship(
        "AnalysisMessage",
        back_populates="dream",
        cascade="all, delete-orphan",
        order_by="AnalysisMessage.created_at"
    )
    
    def __repr__(self) -> str:
        return f"<Dream(id={self.id}, user_id={self.user_id}, title={self.title})>"
