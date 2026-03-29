"""Add subscriptions table and billing fields to users

Revision ID: 004_subscriptions
Revises: 003_temporal
Create Date: 2026-03-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "004_subscriptions"
down_revision = "003_temporal"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # New columns on users
    op.add_column(
        "users",
        sa.Column("trial_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("analyses_week_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("analyses_week_reset_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Subscriptions table
    op.create_table(
        "subscriptions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("product_id", sa.String(128), nullable=False),
        sa.Column("purchase_token", sa.Text(), nullable=False, unique=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("subscriptions")
    op.drop_column("users", "analyses_week_reset_at")
    op.drop_column("users", "analyses_week_count")
    op.drop_column("users", "trial_started_at")
