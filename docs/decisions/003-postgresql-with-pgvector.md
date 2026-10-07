# 003 — PostgreSQL + pgvector for data and embeddings

**Status:** Accepted
**Date:** 2026-10-05
**Deciders:** Basel

## Context

MallMind needs persistent storage for:

1. **Relational data** — malls, floors, locations, map nodes/edges, users, parking records. Clear schema, strong referential integrity needs (foreign keys everywhere), transactional guarantees (parking "current" flag must be consistent).
2. **Full-text / substring search** — "nike", "zara", "sushi" — needs fast `ILIKE '%foo%'` behaviour.
3. **Vector embeddings** — ~a few thousand text chunks about mall policies, store descriptions, FAQ content; retrieved by cosine similarity for RAG.

Constraints:

- One developer; must be easy to operate locally and in production
- Must run in Docker Compose for local dev
- Prefer a managed service in production (Azure Database for PostgreSQL, RDS, etc.)
- Scale: thousands of locations, tens of thousands of edges, low thousands of vector chunks per mall. Decidedly not "big data."

What we're optimizing for: **one database to operate**, strong SQL semantics, acceptable vector performance.

## Options considered

### Option A — PostgreSQL + `pgvector` extension
- **Pros:**
  - Single operational surface — one connection string, one backup, one monitoring dashboard.
  - Full relational power (joins, constraints, transactions) for app data.
  - `pgvector` gives IVFFlat and HNSW indexes for approximate nearest-neighbor search; proven at tens of millions of vectors.
  - `pg_trgm` extension gives GIN-indexed substring search for the keyword branch of hybrid search.
  - Managed everywhere (Azure, AWS, GCP, Supabase, Neon).
  - You can do hybrid search (keyword WHERE + vector ORDER BY) in a single query.
- **Cons:**
  - Not the fastest vector engine at hundreds of millions of embeddings.
  - HNSW builds can be slow on huge datasets (not our scale).

### Option B — PostgreSQL + a dedicated vector DB (Pinecone / Weaviate / Qdrant / Chroma)
- **Pros:**
  - Vector engines are purpose-built; faster at very large scale.
  - Richer vector-side features (metadata filtering optimizations, multi-vector per doc, etc.).
- **Cons:**
  - **Two databases to operate** — two connection pools, two sets of credentials, two monitoring surfaces, two cost lines.
  - Consistency between the two becomes an application concern (what if the embedding insert succeeds but the Postgres insert fails?).
  - Vendor lock-in for Pinecone; self-hosting Weaviate/Qdrant adds ops burden.
  - Cross-system joins ("find chunks about store X") either require filtering in two steps or duplicating metadata into the vector DB.

### Option C — SQLite + a vector extension (e.g., `sqlite-vss`)
- **Pros:** zero ops; file-based; perfect for tiny personal projects.
- **Cons:** no concurrent writers in the production-grade sense; harder to deploy on managed cloud; weaker ecosystem for Python ORM + migrations than Postgres.

### Option D — MongoDB (or another document DB) with Atlas Vector Search
- **Pros:** schemaless, native vector search in Atlas.
- **Cons:** our data is deeply relational (map_edges reference map_nodes which reference floors which reference malls); document DBs make foreign-key integrity the application's job; wrong primitive for a graph-anchored domain.

## Decision

**Option A — PostgreSQL with the `pgvector` extension.** We'll use `pg_trgm` for substring text search and `pgvector` with an HNSW index for semantic similarity.

## Why

1. **One database to operate.** The biggest hidden cost of a second DB is not latency or features — it's the surface area of credentials, backups, migrations, monitoring, and failure modes. Keeping one Postgres instance keeps everything else simpler.
2. **Scale fits comfortably.** Our vector corpus is in the low thousands per mall. `pgvector` with HNSW handles millions of vectors with sub-50ms recall@10. We are not close to needing a specialized engine.
3. **Hybrid search becomes natural.** We can combine `WHERE name ILIKE %q%` with `ORDER BY embedding <=> query_embedding` in a single SQL query — the entire ranking logic lives in the query planner, not scattered across two systems.
4. **Transactional integrity for parking + user data.** The "current parking spot per user" uniqueness is enforceable with a partial unique index. Doing this across two DBs is far harder.
5. **Managed everywhere.** Azure Database for PostgreSQL supports `pgvector` as of 2024. We won't be stuck.
6. **Interview optics.** "I evaluated pgvector against Pinecone and chose pgvector because at my scale the operational cost of a second system outweighed the performance delta" is a stronger answer than defaulting to the trendy choice.

## Trade-offs

| We give up | We accept this because |
|---|---|
| Top-end vector-search performance at huge scale | We're nowhere near that scale. |
| Specialized vector-DB features (e.g., sparse+dense hybrid rerankers built in) | Can implement ranking in-process if ever needed. |
| Lower risk of needing to tune Postgres config for mixed workloads | Monitoring will catch this early; vector workloads for our size are not that heavy. |
| Multi-tenant isolation at the DB level | Row-level security is available if we ever need it. |

## Important configuration notes

(Will become part of the migration / docker-compose files in Phase 0b and Phase 1.)

- Postgres version: **16** (latest stable with mature `pgvector` support).
- Extensions: `pg_trgm`, `pgvector`.
- Vector dimensions: depends on embedding model (OpenAI `text-embedding-3-small` = 1536; `nomic-embed-text` = 768). We'll fix this when the LLM provider is chosen in Phase 5.
- Index type for vectors: **HNSW** (better recall than IVFFlat at the cost of slower build; for a few-thousand-vector corpus this is a no-brainer).

## What would change this later

- **Vector corpus exceeds ~10M embeddings** with strict P95 latency requirements: evaluate Qdrant or a managed vector DB.
- **Mixed workload hotspot**: if vector queries start starving relational queries for buffer cache, consider a dedicated read replica for vector traffic or split them physically.
- **Need for cross-region multi-master writes**: Postgres doesn't do this well; we'd need Spanner-like options or a redesign. Not relevant for a portfolio project.
- **Multi-mall tenancy with strict data isolation**: evaluate schema-per-tenant vs. row-level security vs. a cluster-per-tenant.

## Related

- See [`001-modular-monolith.md`](001-modular-monolith.md) — one DB per deployment follows from one deployable.
- Phase 1 planning (to be written) will cover the full schema and the specific index set.
