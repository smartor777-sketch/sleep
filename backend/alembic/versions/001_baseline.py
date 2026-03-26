"""Baseline: snapshot of existing schema (no-op, DB already up to date).

Revision ID: 001_baseline
Revises: None
Create Date: 2026-03-22
"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing schema created by init_db() / _apply_schema_upgrades().
    # This migration exists only to establish the Alembic version baseline.
    pass


def downgrade() -> None:
    pass
