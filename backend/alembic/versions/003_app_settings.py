"""App settings: key-value таблица для feature flags и конфигурации из админки.

Revision ID: 003_app_settings
Revises: 002_pgvector_rag
Create Date: 2026-08-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_app_settings"
down_revision: Union[str, None] = "002_pgvector_rag"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("key", name="uq_app_settings_key"),
    )
    op.create_index("ix_app_settings_key", "app_settings", ["key"])

    # Семя по-умолчанию: email-авторизация включена.
    op.execute(
        "INSERT INTO app_settings (id, key, value, updated_at) "
        "VALUES (gen_random_uuid(), 'email_auth_enabled', 'true', now())"
    )


def downgrade() -> None:
    op.drop_index("ix_app_settings_key", table_name="app_settings")
    op.drop_table("app_settings")