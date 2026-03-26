"""Baseline: create full initial schema.

Revision ID: 001_baseline
Revises: None
Create Date: 2026-03-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from alembic import op

revision: str = "001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=True, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("is_anonymous", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("device_id", sa.String(255), nullable=True, unique=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("email_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_admin", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("sub_type", sa.String(16), nullable=False, server_default="free"),
        sa.Column("sub_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("self_description", sa.Text, nullable=True),
        sa.Column("onboarding_completed", sa.Boolean, nullable=False, server_default="false"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_device_id", "users", ["device_id"])

    # ------------------------------------------------------------------
    # user_archetypes
    # ------------------------------------------------------------------
    op.create_table(
        "user_archetypes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "name", name="uq_user_archetype_name"),
    )
    op.create_index("ix_user_archetypes_user_id", "user_archetypes", ["user_id"])
    op.create_index("ix_user_archetypes_name", "user_archetypes", ["name"])

    # ------------------------------------------------------------------
    # oauth_identities
    # ------------------------------------------------------------------
    op.create_table(
        "oauth_identities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_subject", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("provider", "provider_subject", name="uq_provider_subject"),
    )
    op.create_index("ix_oauth_identities_user_id", "oauth_identities", ["user_id"])
    op.create_index("ix_oauth_identities_provider", "oauth_identities", ["provider"])

    # ------------------------------------------------------------------
    # email_verifications
    # ------------------------------------------------------------------
    op.create_table(
        "email_verifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_email_verifications_user_id", "email_verifications", ["user_id"])
    op.create_index("ix_email_verifications_token", "email_verifications", ["token"])

    # ------------------------------------------------------------------
    # password_resets
    # ------------------------------------------------------------------
    op.create_table(
        "password_resets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_password_resets_user_id", "password_resets", ["user_id"])
    op.create_index("ix_password_resets_token", "password_resets", ["token"])

    # ------------------------------------------------------------------
    # dreams
    # ------------------------------------------------------------------
    op.create_table(
        "dreams",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(64), nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("emoji", sa.String(10), nullable=False, server_default=""),
        sa.Column("comment", sa.String(256), nullable=False, server_default=""),
        sa.Column("gradient_color_1", sa.String(7), nullable=True),
        sa.Column("gradient_color_2", sa.String(7), nullable=True),
        sa.Column("embedding_text", sa.Text, nullable=True),
        sa.Column("embedding_model", sa.String(128), nullable=True),
        sa.Column("embedding_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_dreams_user_id", "dreams", ["user_id"])
    op.create_index("ix_dreams_recorded_at", "dreams", ["recorded_at"])

    # ------------------------------------------------------------------
    # analyses
    # ------------------------------------------------------------------
    op.create_table(
        "analyses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("dream_id", UUID(as_uuid=True), sa.ForeignKey("dreams.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("result", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_analyses_dream_id", "analyses", ["dream_id"])
    op.create_index("ix_analyses_user_id", "analyses", ["user_id"])
    op.create_index("ix_analyses_status", "analyses", ["status"])
    op.create_index("ix_analyses_celery_task_id", "analyses", ["celery_task_id"])

    # ------------------------------------------------------------------
    # dream_chunks  (temporal fields added in 003_temporal)
    # ------------------------------------------------------------------
    op.create_table(
        "dream_chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("dream_id", UUID(as_uuid=True), sa.ForeignKey("dreams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("embedding_text", sa.Text, nullable=True),
        sa.Column("embedding_model", sa.String(128), nullable=True),
        sa.Column("metadata_json", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_dream_chunks_dream_id", "dream_chunks", ["dream_id"])
    op.create_index("ix_dream_chunks_user_id", "dream_chunks", ["user_id"])

    # ------------------------------------------------------------------
    # analysis_messages
    # ------------------------------------------------------------------
    op.create_table(
        "analysis_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dream_id", UUID(as_uuid=True), sa.ForeignKey("dreams.id", ondelete="CASCADE"), nullable=True),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_analysis_messages_user_created", "analysis_messages", ["user_id", "created_at"])
    op.create_index("ix_analysis_messages_user_dream_created", "analysis_messages", ["user_id", "dream_id", "created_at"])

    # ------------------------------------------------------------------
    # dream_symbols
    # ------------------------------------------------------------------
    op.create_table(
        "dream_symbols",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dream_id", UUID(as_uuid=True), sa.ForeignKey("dreams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_id", UUID(as_uuid=True), sa.ForeignKey("dream_chunks.id", ondelete="CASCADE"), nullable=True),
        sa.Column("symbol_name", sa.String(128), nullable=False),
        sa.Column("weight", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_dream_symbols_user_id", "dream_symbols", ["user_id"])
    op.create_index("ix_dream_symbols_dream_id", "dream_symbols", ["dream_id"])
    op.create_index("ix_dream_symbols_chunk_id", "dream_symbols", ["chunk_id"])
    op.create_index("ix_dream_symbols_symbol_name", "dream_symbols", ["symbol_name"])

    # ------------------------------------------------------------------
    # dream_archetypes
    # ------------------------------------------------------------------
    op.create_table(
        "dream_archetypes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dream_id", UUID(as_uuid=True), sa.ForeignKey("dreams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("archetype_name", sa.String(128), nullable=False),
        sa.Column("delta", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_dream_archetypes_user_id", "dream_archetypes", ["user_id"])
    op.create_index("ix_dream_archetypes_dream_id", "dream_archetypes", ["dream_id"])
    op.create_index("ix_dream_archetypes_archetype_name", "dream_archetypes", ["archetype_name"])

    # ------------------------------------------------------------------
    # dream_symbol_entities
    # ------------------------------------------------------------------
    op.create_table(
        "dream_symbol_entities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dream_id", UUID(as_uuid=True), sa.ForeignKey("dreams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_id", UUID(as_uuid=True), sa.ForeignKey("dream_chunks.id", ondelete="CASCADE"), nullable=True),
        sa.Column("canonical_name", sa.String(128), nullable=False),
        sa.Column("display_label", sa.String(128), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False, server_default="symbol"),
        sa.Column("weight", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("related_archetypes_json", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_dream_symbol_entities_user_id", "dream_symbol_entities", ["user_id"])
    op.create_index("ix_dream_symbol_entities_dream_id", "dream_symbol_entities", ["dream_id"])
    op.create_index("ix_dream_symbol_entities_chunk_id", "dream_symbol_entities", ["chunk_id"])
    op.create_index("ix_dream_symbol_entities_canonical_name", "dream_symbol_entities", ["canonical_name"])


def downgrade() -> None:
    op.drop_table("dream_symbol_entities")
    op.drop_table("dream_archetypes")
    op.drop_table("dream_symbols")
    op.drop_table("analysis_messages")
    op.drop_table("dream_chunks")
    op.drop_table("analyses")
    op.drop_table("dreams")
    op.drop_table("password_resets")
    op.drop_table("email_verifications")
    op.drop_table("oauth_identities")
    op.drop_table("user_archetypes")
    op.drop_table("users")
