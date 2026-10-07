"""Search passages and pgvector embeddings for locations.

Revision ID: 0002_location_documents
Revises: 0001_initial_schema
Create Date: 2026-10-06
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0002_location_documents"
down_revision: str | Sequence[str] | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        """
        CREATE TABLE location_documents (
            location_id UUID PRIMARY KEY
                REFERENCES locations (id) ON DELETE CASCADE,
            search_text TEXT NOT NULL,
            content_hash CHAR(64) NOT NULL,
            embedding_model VARCHAR(128),
            embedding vector(384),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX ix_location_documents_embedding
            ON location_documents
            USING hnsw (embedding vector_cosine_ops)
        """
    )
    op.execute(
        """
        CREATE INDEX ix_locations_name_trgm
            ON locations
            USING gin (lower(name) gin_trgm_ops)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_locations_name_trgm")
    op.execute("DROP TABLE IF EXISTS location_documents")
