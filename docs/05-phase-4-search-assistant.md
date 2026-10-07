# 05 — Phase 4: Hybrid search and a mall assistant

**Status:** Implemented on portable PostgreSQL 16.15 with the local MiniLM embedder. Live chat-model verification is **pending** (`LLM_API_KEY` is not set). Phase 5 is the shopping tour in `06-phase-5-shopping-route.md`.
**Date:** 2026-10-06.

The assistant is a client of search and of A*. It is not a second catalog and it does not compute routes.

---

## 1. Search architecture

Three query shapes, three techniques:

| Shape | Example | What works |
|---|---|---|
| Exact | Nike, ATM | Equality and prefix |
| Typo | Nkie, restrom | One edit, or `pg_trgm` when the string is long enough |
| Conceptual | running shoes, withdraw money, مكان للصلاة | Curated synonyms, then vectors if nothing lexical hit |

Exact SQL misses typos and paraphrases. Trigrams miss paraphrases and, on 4-letter brands, miss transpositions (`similarity('nkie','nike') = 0.11`). Vectors match concepts and also match the wrong neighbor. The hybrid is in [ADR-011](decisions/011-hybrid-lexical-and-vector-search.md).

`GET /api/v1/search?q=` returns id, name, slug, category, floor, score, match type. It does not return vectors. Empty query → 400 `empty_query`. Over 200 characters → 400 `query_too_long`. No hits → 200 and `results: []`.

If the embedder or pgvector throws, the handler returns the lexical hits and sets `semantic` to `unavailable`. If a lexical band already decided, `semantic` is `skipped` and the model is not called. A one- or two-token miss ("Gucci") is `skipped` as well: we will refuse it, so we do not embed it.

---

## 2. Lexical ranking

Bands, highest first. The numbers are fences, not weights. A later band cannot pass an earlier one.

```
exact name/slug     1.00
name as a token     0.96
prefix              0.90
trigram / one edit  0.75 .. 0.85   (one edit is the fixed point 0.80)
category            0.70
keyword             0.60
```

`pg_trgm` similarity in [0.3, 1] is scaled into (0.75, 0.85]. 0.3 is the extension's own cutoff. The 0.10 width only sorts two typos. See [the trigram note](debugging/2026-10-06-trigram-short-name.md) for why "Nkie" is not in that range.

---

## 3. Semantic search

An embedding is a list of 384 numbers. Texts the model was trained to treat as similar land at a small angle. Cosine similarity is that angle, independent of vector length. It can match "withdraw money" to an ATM passage without sharing a token. It does not know NOVA Mall. It only knows the passage we stored.

Passage, one per location: name, slug, category in English / Arabic / Hebrew, description, and a short synonym list. "jogging" is not in the list, so a paraphrase has to come from the model.

Stored in `location_documents.embedding vector(384)` with an HNSW index (`vector_cosine_ops`). 31 rows. pgvector is enough. A second database would be a second source of truth. [ADR-003](decisions/003-postgresql-with-pgvector.md), [ADR-012](decisions/012-embedding-provider-abstraction.md).

Cosine floor **0.38**, from this mall and this model, not from a blog:

- "running shoes" → Nike 0.435, Adidas 0.389
- "withdraw money" → the three ATMs ≈ 0.443–0.445
- query "Nike" → Adidas 0.441, Nike 0.388
- "footwear for jogging today" → Adidas 0.450, Nike 0.431
- "Gucci" → Sushi Kaito 0.427
- "כספומט" → Muji 0.336 (wrong store, and under the floor)
- "مكان للصلاة" → 0.247 (no prayer room; stays empty)

Reindex: `python -m app.search.reindex`. On 2026-10-06: `written=31 skipped=0 embed_failures=0`, model `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. A row is skipped when hash + model + vector already match. A failed call does not erase the previous vector.

---

## 4. Hybrid strategy

1. Score every location lexically.
2. If the best hit is exact, prefix, trigram, category, or keyword, keep that order. Append unseen vector hits only for display. Do not call the embedder.
3. If nothing lexical hit and the query has fewer than 3 content tokens, return empty.
4. Otherwise embed the query, take neighbors with cosine ≥ 0.38, and merge with Reciprocal Rank Fusion (k=60) when both lists exist.

RRF compares ranks, not the 0.60 keyword score with a 0.44 cosine. We do not use it on a gated list, because those scales are already ordered on purpose.

Alternatives we did not ship: a learned blend (no labels beyond 13 queries), "whichever returns first" (races a wrong neighbor against a right name), vector-only (loses "Nike").

---

## 5. Evaluation

`python -m app.evaluation`. Thirteen search queries, nine assistant prompts. English, Arabic, Hebrew. NOVA has no prayer room and no Gucci. Those must be empty.

Measured 2026-10-06, local MiniLM, seeded database, no chat key:

| Mode | top-1 | top-3 |
|---|---|---|
| Lexical | 12/13 | 12/13 |
| Semantic | 8/13 | 10/13 |
| Hybrid | 12/13 | 13/13 |

Lexical misses only "footwear for jogging today" (not a synonym). Semantic additionally misses the typo "Nkie" (best cosine 0.259), the bare Hebrew token "כספומט", returns Adidas for "Nike", and returns Sushi Kaito for "Gucci". Hybrid keeps the lexical answers and, on the jogging line, puts Nike in the top 3 behind Adidas. That 0.019 gap is the result. It is not a tuned success.

Assistant grounding on templates: **9/9**. Tool selection matched the case (search, route, avoid-stairs profile, nearest restroom). Live LLM: pending.

---

## 6. Assistant, RAG, and tools

Four different jobs:

| Job | Who does it |
|---|---|
| Retrieval | Lexical / vector search over `location_documents` |
| Tool call | Python (`search_locations`, `get_location`, `calculate_route`) |
| Business logic | `NavigationService` A*. The model never sees the graph. |
| Language | Template, or the chat model phrasing a fact sheet we already built |

The model is not asked to choose tools. Empty retrieval does not call it. Route text is always the template, so a distance cannot be invented. The system prompt is `app/assistant/prompts/system_v1.txt`.

`POST /api/v1/assistant/query` accepts `message`, optional `current_location_id`, and `routing_profile` (`standard` is an alias of `normal`). The response is `answer`, `language`, `sources`, `actions`, `llm` (`template` / `provider` / `unavailable` / `rejected`), `tools`.

Actions the map already understands: `highlight_location`, `change_floor`, `show_route`.

---

## 7. Hallucinations

Controls we actually run:

- Unknown name, one or two tokens: no vector neighbor, no model call, sources empty.
- Phrased text that names another mall store, or an English Capitalized word that is not in the sources or a small allow-list, is discarded. The template remains.
- Opening hours, prices, and stores that are not in Postgres are not in the fact sheet, so the template cannot mention them.
- Routes quote `distance_m` from A*.

We do not claim this makes hallucinations impossible. The guard is a denylist of known names, not a proof. A model can still misstate a floor we did retrieve if the wording sneaks past the capital-word check. Rejected output is logged as `llm=rejected` and the user sees the template.

Checked: "Where is Gucci?", "وين Gucci؟", "איפה Gucci?" → refusal in that language, no sources. Browser: "Where is Gucci?" rendered "I couldn't find that location in NOVA Mall."

---

## 8. Languages

Script detection: Arabic block → `ar`, Hebrew block → `he`, otherwise `en`. The reply uses that language. Store names stay as seeded ("Nike", "Main Entrance", "ATM — Ground"). Floor names are the seed's English names. Route instructions ("Walk 80 m") are the router's English strings inside an Arabic or Hebrew sentence.

Browser, 2026-10-06:

- "Take me to Nike" → "Main Entrance → Nike: 102 m, about 1 min. Walk 102 m", A* , 13 nodes, Nike highlighted.
- "איפה הכספומט?" → "ATM — Ground נמצא בGround Floor (ATM)." Card switched to that ATM.
- "وين أقرب حمام؟" → Arabic sentence, "Restroom — Ground South", 80 m, A* 7 nodes.
- Search "Nkie" → Nike, click highlights it.

`dir="rtl"` is set on the answer when the language is `ar` or `he`.

Limitation: a Hebrew sentence that only uses Latin letters ("where is Nike" typed in an English UI) is answered in English. Mixed script follows the first Arabic or Hebrew character. We do not translate the catalog.

---

## 9. Frontend

The existing explorer gained an Ask tab. Quick prompts: find Nike, nearest bathroom, wheelchair route to Nike, where is an ATM, where did I start, take me to Nike. `show_route` calls the same `runRoute` the Route tab uses. Search still filters names locally and, after 250 ms, merges backend hits. If `/search` fails, the local list remains.

---

## 10. Failure, cost, security

| Failure | Behavior |
|---|---|
| Embedder missing or throwing | Lexical results, `semantic=unavailable` |
| pgvector error | Same |
| Chat model missing | `llm=template` |
| Chat model HTTP error | `llm=unavailable`, template text |
| Ungrounded model text | `llm=rejected`, template text |
| No route | Template, no `show_route` |
| Empty query / over 200 chars (search) or 500 (assistant) | 400 |

In-process sliding window: search 60/min, assistant 20/min, per process. Not Redis. Logs: mall, query length, hit counts, semantic state, language, tool names, latency, source count, llm mode. Not the API key. Not the raw message.

Cost: embeddings are built at reindex, skipped when the hash matches, and skipped on search when lexical already decided or the query is a short miss. The chat model is not called for routes, refusals, or when no key is set. Fact sheets are one to three locations, not the mall.

Prompt injection is not solved. Limits we do have: length caps, rate limit, the model cannot call the router, route numbers are not model text, and a phrased answer that names a store outside the fact sheet is dropped.

---

## 11. Tests

| Check | Result |
|---|---|
| `ruff check` and `ruff format --check` | Passed |
| `pytest` with `DATABASE_URL` set, `EMBEDDING_PROVIDER=none` | **98 passed** |
| Frontend lint, `tsc --noEmit` | Passed |
| Vitest | **14 passed** |
| `next build` | Passed, First Load JS **110 kB** |
| Reindex | 31/31, 0 failures |
| `python -m app.evaluation` | Numbers in §5 |
| Browser | Route, refusal, Hebrew ATM, Arabic nearest restroom, Nkie → Nike |
| Chat provider | Pending. Closed-port test and a raising fake both fall back to the template. |

CI does not download MiniLM and does not call a paid API. Semantic quality is the eval script.

---

## 12. What Phase 5 should not be

More model surface. The next user-visible gap was a multi-stop tour on the router we already trust. That work is Phase 5, recorded separately. Do not extend the assistant from this document.
