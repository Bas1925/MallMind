# 012 — One embedding provider, local by default

**Status:** Accepted
**Date:** 2026-10-06
**Deciders:** Basel

## Context

Search and reindex need vectors. The rest of the backend must not import a vendor SDK. Tests must not download a model or spend money. A missing provider must not take lexical search down.

## Options considered

### Option A — Call fastembed from the search service
- Pros: fewer files.
- Cons: the search service learns ONNX, and a unit test cannot substitute a vector.

### Option B — `EmbeddingProvider` with `embed_text` / `embed_many`
- Pros: search, reindex, and tests share one call. `local` is fastembed (MiniLM, 384 dims, no key). `openai` is an HTTP POST when `LLM_API_KEY` and `LLM_BASE_URL` are set. `none` disables vectors. `HashEmbeddingProvider` exists only for the pgvector ordering test and is not semantic.
- Cons: a second implementation to keep honest. The HTTP one is unused until a key exists.

## Decision

Option B. Configuration is environment variables. No key is committed.

`python -m app.search.reindex` loads each location's passage (name, category in three languages, description, curated synonyms), embeds it, and upserts `location_documents`. A row is skipped when the content hash, model name, and stored vector already match. A failed embed writes the passage with `embedding = COALESCE(new, old)` so a bad call cannot wipe a good vector.

## Why

31 locations do not justify a vector database or an embedding call on every "Nike" keystroke. The search service skips the provider when a lexical band already decided, and it skips one- and two-token misses such as "Gucci" so we do not pay to compute a neighbor we will throw away.

## Trade-offs

The default model is multilingual and still weak on a single Hebrew token (see the eval). Swapping models means a reindex, because the hash includes the model name and the column is `vector(384)`. A 1536-dim API model does not fit this column. That is deliberate.

## What would change this later

An API model we have actually evaluated on the same 13 queries, with a migration to a new dimension. Not a config flag alone.
