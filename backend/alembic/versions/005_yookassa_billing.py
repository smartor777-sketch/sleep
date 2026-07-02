"""Switch billing subscriptions to provider payment ids

Revision ID: 005_yookassa_billing
Revises: 004_subscriptions
Create Date: 2026-06-26
"""
from alembic import op


revision = "005_yookassa_billing"
down_revision = "004_subscriptions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "subscriptions",
        "purchase_token",
        new_column_name="provider_payment_id",
    )


def downgrade() -> None:
    op.alter_column(
        "subscriptions",
        "provider_payment_id",
        new_column_name="purchase_token",
    )
