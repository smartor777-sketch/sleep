"""Add temporal fields to dream_chunks

Revision ID: 003
Revises: 002
Create Date: 2026-03-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add nullable columns first
    op.add_column(
        "dream_chunks",
        sa.Column("source_recorded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "dream_chunks",
        sa.Column("source_created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "dream_chunks",
        sa.Column("source_order", sa.Integer(), nullable=True),
    )

    # Backfill from dreams table
    op.execute(
        """
        UPDATE dream_chunks dc
        SET source_recorded_at = d.recorded_at,
            source_created_at  = d.created_at,
            source_order       = dc.chunk_index
        FROM dreams d
        WHERE dc.dream_id = d.id
        """
    )

    # Backfill any orphans (shouldn't exist, but safety)
    op.execute(
        """
        UPDATE dream_chunks
        SET source_recorded_at = COALESCE(source_recorded_at, created_at),
            source_created_at  = COALESCE(source_created_at, created_at),
            source_order       = COALESCE(source_order, chunk_index)
        WHERE source_recorded_at IS NULL
           OR source_created_at IS NULL
           OR source_order IS NULL
        """
    )

    # Now set NOT NULL
    op.alter_column("dream_chunks", "source_recorded_at", nullable=False)
    op.alter_column("dream_chunks", "source_created_at", nullable=False)
    op.alter_column("dream_chunks", "source_order", nullable=False)


def downgrade() -> None:
    op.drop_column("dream_chunks", "source_order")
    op.drop_column("dream_chunks", "source_created_at")
    op.drop_column("dream_chunks", "source_recorded_at")
