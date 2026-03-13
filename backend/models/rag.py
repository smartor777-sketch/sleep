"""RAG-related models for dream memory."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class DreamChunk(Base):
    """Semantic chunk extracted from a dream."""

    __tablename__ = "dream_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    dream_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dreams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    dream: Mapped["Dream"] = relationship("Dream", back_populates="chunks")


class DreamSymbol(Base):
    """Normalized symbol extracted from a dream or a dream chunk."""

    __tablename__ = "dream_symbols"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dream_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dreams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dream_chunks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    symbol_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    weight: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    dream: Mapped["Dream"] = relationship("Dream", back_populates="symbols")
    chunk: Mapped["DreamChunk | None"] = relationship("DreamChunk")


class DreamArchetype(Base):
    """Archetype delta attributed to a concrete dream."""

    __tablename__ = "dream_archetypes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dream_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dreams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    archetype_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    delta: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    dream: Mapped["Dream"] = relationship("Dream", back_populates="dream_archetypes")


class DreamSymbolEntity(Base):
    """Human-readable symbolic entity extracted by LLM for Dream Map."""

    __tablename__ = "dream_symbol_entities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dream_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dreams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dream_chunks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    canonical_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    display_label: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False, default="symbol")
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    related_archetypes_json: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    dream: Mapped["Dream"] = relationship("Dream", back_populates="symbol_entities")
    chunk: Mapped["DreamChunk | None"] = relationship("DreamChunk")
