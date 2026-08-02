"""pgvector RAG: vector column + HNSW index for dream_chunks.

Revision ID: 002_pgvector_rag
Revises: 001_baseline
Create Date: 2026-08-02
"""
from typing import Sequence, Union

from alembic import op

revision: str = "002_pgvector_rag"
down_revision: Union[str, None] = "001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Матч с settings.embeddings_dimensions (Gemini embedding-001, output 768).
EMBED_DIM = 768


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        f"ALTER TABLE dream_chunks ADD COLUMN IF NOT EXISTS embedding_vec vector({EMBED_DIM})"
    )
    # HNSW (Hierarchical Navigable Small World) — O(log N) косинусный поиск.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_dream_chunks_embedding_vec " 
        f"ON dream_chunks USING hnsw (embedding_vec vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_dream_chunks_embedding_vec")
    op.execute("ALTER TABLE dream_chunks DROP COLUMN IF EXISTS embedding_vec")
    # Расширение не откатываем — оно безопасно остаётся в БД.