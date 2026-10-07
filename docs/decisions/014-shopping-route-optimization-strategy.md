# 014 — Open tour: Held-Karp while it is cheap, then Nearest Neighbor + 2-opt

**Status:** Accepted
**Date:** 2026-10-06
**Deciders:** Basel

## Context

A shopper picks several stores. A* already prices one pair. The new question is the visit order. The walk should not be forced back to the entrance. The mall graph is directed (ADR-008), and wheelchair mode deletes edges before the search (the same filter as a single route).

## Options considered

### Option A — Permutations for every request
- **Pros:** obviously optimal; easy to test.
- **Cons:** 10 stops is 3.6 million orders, and each order still needs its pairs. 20 stops is 2.43 × 10^18. Not a request handler.

### Option B — Nearest Neighbor + 2-opt for every request
- **Pros:** `O(k^2)` greedy, then a local search that cannot increase the cost. Fine at 20 stops (mean 118 ms on NOVA, mostly A*).
- **Cons:** on the canonical NOVA list, 2-opt made 0 moves and sat 4 m / 1.0% above the optimum (386.5 m vs 382.5 m). Shipping only the heuristic would hide that gap.

### Option C — Held-Karp up to a measured cutoff, heuristic after that
- **Pros:** exact when the DP is still a small part of the request; a number for the heuristic gap on every small list; the matrix code does not change.
- **Cons:** two solvers to keep honest. The cutoff is a policy, and it will move if the machine or the graph changes.

## Decision

**Option C.** Open tour. Start fixed. No return leg. No required final stop in this phase.

Held-Karp for `k ≤ 12`. Nearest Neighbor + 2-opt above that. Hard cap 20 stops.

The cutoff is the 2026-10-06 timing on random directed matrices: 17 ms at 10 stops, 89 ms at 12, 543 ms at 14. Twelve is still one click. Fourteen is not.

2-opt reprices reversed internal edges. The symmetric boundary-only delta is wrong on this graph. See the debugging note.

If a stop is unreachable under the selected profile, the plan fails and names it. The solver never skips a row.

A candidate order replaces the submitted order only when it is strictly cheaper (more than 1 cm, or the time equivalent). Otherwise the API says no shorter route was found.

## Why

1. The interview-relevant fact is the gap, not a slogan that the route is optimal. Small lists can show exact versus heuristic because both ran.
2. Pair costs depend on the profile. Building the matrix with that profile means the order and the drawn path cannot disagree.
3. Caching pairs inside the request is enough. `n × (n - 1)` A* calls at 20 stops is 420, and the mean request was 118 ms. Redis would not change the algorithm.

## Trade-offs

| We give up | We accept this because |
|---|---|
| Exact answers above 12 stops | 14 stops of DP was 543 ms before the A* matrix. |
| A required end door | Open tour matches "finish at the last shop". A fixed end is a later constraint, not a different architecture. |
| Guaranteed optimality of 2-opt | The NOVA sample at 7 stops still shows the mean gap falling from 10.5% to 2.4%, and the canonical list shows the leftover 4 m. |

## What would change this later

- If a 12-stop NOVA request stops feeling instant, lower `EXACT_MAX_STOPS` and re-benchmark. Do not guess.
- If shoppers must end at a specific door, add that node as a fixed end in the DP and the heuristic. Do not bolt a return-to-start onto the open tour.
- If 20 stops of pairwise A* dominates, reuse pairs across requests only with a measured invalidation story. Still not Redis by default.
