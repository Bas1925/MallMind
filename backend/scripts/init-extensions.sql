-- =============================================================================
-- MallMind — Postgres extension bootstrap
-- =============================================================================
-- Runs once, on first database initialization. Mounted into
-- /docker-entrypoint-initdb.d/ by docker-compose.
--
-- Install both extensions MallMind depends on:
--   pgvector  : HNSW / IVFFlat indexes for RAG vector similarity
--   pg_trgm   : GIN trigram indexes for fast `ILIKE` text search
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
