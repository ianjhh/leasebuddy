"""Add HNSW index on lease_chunks.embedding

The index is declared in app/models/lease.py, but `Base.metadata.create_all`
only creates indexes when it creates the table. Any database whose tables
predate the declaration -- including every database built with `alembic
upgrade`, since the initial migration never created it -- has been running
vector search as a sequential scan.

Revision ID: a1f4c9d2e8b7
Revises: db1bdebbbfbf
Create Date: 2026-09-07

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1f4c9d2e8b7'
down_revision: str | Sequence[str] | None = 'db1bdebbbfbf'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the HNSW index used by the cosine-distance (<=>) queries."""
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_chunk_embedding_hnsw "
        "ON lease_chunks USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    """Drop the HNSW index."""
    op.execute("DROP INDEX IF EXISTS ix_chunk_embedding_hnsw")
