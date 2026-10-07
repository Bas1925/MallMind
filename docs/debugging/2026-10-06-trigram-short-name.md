# 2026-10-06 — pg_trgm similarity("nkie", "nike") is 0.11

**Severity:** medium
**Time to find:** ~20 minutes (the test failed, the first SQL probe died in PowerShell quoting)
**Area:** search

## Symptom

`GET /api/v1/search?q=Nkie` returned `results: []`. The test expected Nike.

## Hypothesis path

1. The ranker required `similarity >= 0.3` and the SQL never returned Nike. Ruled out: the query loads every active location and scores in Python. Nike was in the list.
2. The cutoff itself was the bug. Measured in psql-via-psycopg, not by guessing:

| Query | Best name | similarity |
|---|---|---|
| nkie | Nike | 0.111 |
| nkie | NOVA Cinema | 0.063 |
| restrom | Restroom — Level 1 | 0.389 |
| starbuks | Starbucks | 0.583 |
| gucci | Guest Services | 0.105 |

"restrom" and "starbuks" already clear 0.3. "nkie" does not. Lowering the global cutoff to 0.10 would also accept Guest Services for "Gucci" (0.105), which is the false friend we cannot ship.

## Root cause

pg_trgm pads strings and compares trigram sets. On a 4-letter word, one adjacent transposition (`nkie` / `nike`) replaces almost every trigram, so the score collapses under the default 0.3 cutoff. The strings are still one Damerau edit apart. "gucci" vs "guest" is three substitutions.

## Fix

If the query is at least 4 characters and one edit from the folded name or slug, score 0.80 with match type `trigram`. That sits in the existing trigram band: below prefix 0.90, above category 0.70. Longer typos keep using pg_trgm. `tests/test_search_rank.py` covers Nkie at similarity 0.11 and Gucci against Guest Services.

## Prevention

The unit test passes a measured 0.11, not a flattering 0.5.

## Lesson

A library cutoff is a property of the strings you have, not a constant you copy from the docs. Short brand names are the worst case for trigrams.
