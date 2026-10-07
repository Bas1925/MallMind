# 011 — Hybrid lexical search with a vector fallback

**Status:** Accepted
**Date:** 2026-10-06
**Deciders:** Basel

## Context

Mall queries are not one problem.

- Exact / lexical: "Nike", "ATM".
- Typo: "Nkie", "restrom".
- Conceptual: "running shoes", "withdraw money", "مكان للصلاة".

Exact SQL misses typos and paraphrases. `pg_trgm` catches many typos and still cannot see that "withdraw money" means an ATM. A vector nearest-neighbor will answer the paraphrase and will also answer "Nike" with Adidas (measured cosine 0.441 vs Nike's own passage at 0.388) and "Gucci" with Sushi Kaito (0.427). One technique is the wrong product.

## Options considered

### Option A — Lexical only
- Pros: deterministic, no model, no API cost.
- Cons: "footwear for jogging today" returns nothing. That query is not in the synonym list on purpose.

### Option B — Vector only
- Pros: paraphrases.
- Cons: loses known store names to a neighbor. Measured on this mall.

### Option C — Run both and Reciprocal Rank Fusion always
- Pros: one formula (k=60, Cormack / Clarke / Buettcher, SIGIR 2009).
- Cons: an uncalibrated cosine can outrank an exact name. That is the failure we measured.

### Option D — Lexical bands first, vectors only when lexical missed
- Pros: exact, prefix, trigram, category, and curated keywords cannot be reordered. Vectors are for the leftover paraphrase. Short unknown names ("Gucci", one token) return empty instead of a neighbor.
- Cons: a paraphrase that shares a keyword with the wrong store never reaches the vector list. We accepted that. Keywords are a decision.

## Decision

Option D. Score bands, not a weighted blend:

| Band | Score | Why that number |
|---|---|---|
| Exact name or slug | 1.00 | The query is the place. |
| Name as its own token | 0.96 | "Where is Nike?" still contains the name. |
| Prefix | 0.90 | "Nik" is more specific than a typo. |
| Trigram / one edit | 0.75–0.85, or 0.80 for one edit | Below prefix, above category. The 0.10 width only orders two typos. |
| Category | 0.70 | "food" lists food, not one keyword store. |
| Keyword | 0.60 | Curated synonym. Must not beat a category or a name. |

`pg_trgm` similarity is mapped from [0.3, 1] into (0.75, 0.85]. 0.3 is pg_trgm's default cutoff. A 4-letter transposition is handled separately: `similarity('nkie','nike')` is 0.11, so the cutoff would drop Nike. One insertion, deletion, substitution, or adjacent swap scores 0.80. "Gucci" vs "Guest Services" is not one edit (trigram 0.105, distance > 1).

RRF is used only when the lexical list is not gated and the query is long enough to be a paraphrase. In the 13-query set that path is "footwear for jogging today".

## Why

The 2026-10-06 eval on the seeded mall, model `paraphrase-multilingual-MiniLM-L12-v2`:

| Mode | top-1 | top-3 |
|---|---|---|
| Lexical | 12/13 | 12/13 |
| Semantic | 8/13 | 10/13 |
| Hybrid | 12/13 | 13/13 |

Lexical and hybrid miss the same top-1: the jogging paraphrase, where Adidas (0.450) beat Nike (0.431). Hybrid top-3 includes Nike. Semantic top-1 for the query "Nike" is Adidas. Semantic top-1 for "Gucci" is Sushi Kaito. Hybrid returns Nike and returns nothing for Gucci.

## Trade-offs

Keyword misses never get a vector vote. The cosine floor (0.38) does not, by itself, reject Gucci. The short-query rule does. We do not claim the floor is a universal constant. It sits under the paraphrase cluster we measured (~0.43–0.45) and above prayer-room noise (0.247) and the Hebrew token "כספומט" (peak 0.336, and the nearest store was Muji).

## What would change this later

A model whose "Nike" query ranks Nike above every other store could loosen the lexical gate. A mall with thousands of locations could make the full-table lexical scan worth a trigram index filter in SQL. We already have the GIN index. The scan is 31 rows.
