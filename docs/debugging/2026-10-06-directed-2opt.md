# 2026-10-06 — 2-opt used a symmetric delta on a directed mall

**Severity:** medium
**Time to find:** the first unit run, about ten minutes to see why both assertions failed together
**Area:** navigation

## Symptom

`tests/test_tour.py` failed in two directions at once. On the trap matrix, 2-opt reported 0 moves, so it never left the greedy tour (cost 102). On the tour Held-Karp had already proved optimal, 2-opt reported 1 move.

## Hypothesis path

1. The move cap or the "strictly negative" check was too tight. Ruled out: the optimal tour was being changed, so the search was willing to move.
2. The start-index guard was reversing the wrong span. Ruled out by printing the span: the delta itself was the wrong sign.

## Root cause

The textbook 2-opt delta for a symmetric TSP only replaces the two edges that enter and leave the reversed span. Internal edges are the same length backwards, so they cancel.

MallMind's matrix is directed. Reversing `i..j` replaces every internal edge `cost[a][b]` with `cost[b][a]`. Escalators are one row, not two. The symmetric delta both missed the reversal that drops the trap from 102 to 4 and accepted a reversal that was not cheaper.

## Fix

`_reversal_delta` sums the reversed internal edges and the two boundary edges. After that:

- Trap: Nearest Neighbor `[0, 1, 2, 3]` cost 102. 2-opt `[0, 2, 3, 1]` cost 4, 2 moves. That matches Held-Karp on this fixture. It is not a general proof.
- Optimal input: 0 moves.
- Canonical NOVA list (Main Entrance, Nike, Zara, Apple, ATM Ground, Super-Pharm): 2-opt still 0 moves, 386.5 m, exact 382.5 m.

## Prevention

The unit test keeps both cases: a greedy tour that must not get worse, and an optimal tour that must not move. Held-Karp is checked against brute force on three matrices, including a 5-node one.
