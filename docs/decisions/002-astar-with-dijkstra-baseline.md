# 002 — A* for production, Dijkstra as baseline

**Status:** Accepted
**Date:** 2026-10-05
**Deciders:** Basel

## Context

MallMind needs shortest-path routing on a weighted, directed, multi-floor mall graph with up to a few thousand nodes. We have `(x, y, floor)` coordinates for every node, so we have access to a natural geometric heuristic.

Hard constraints:

- Non-negative edge weights (walking distance, elevator wait time)
- Multiple cost modes (distance-optimal, time-optimal, accessibility-constrained)
- Must return a *correct* shortest path, not a "reasonable" one, when a path exists
- Must return "no route found" (not crash) when the graph is disconnected for the requested mode

What we're optimizing for: **correctness first, latency second, learning value third.**

## Options considered

### Option A — Dijkstra only
- **Pros:** no heuristic to design; one algorithm to test; works whether or not we have coordinates; the textbook starting point.
- **Cons:** explores uniformly outward from the start, so it does strictly more work than A* when a good heuristic is available; wastes the fact that we have (x, y) coordinates.

### Option B — A* only
- **Pros:** typically visits far fewer nodes than Dijkstra when the heuristic is admissible and informative; same worst-case complexity but much better in practice; uses our coordinate data.
- **Cons:** correctness depends on the heuristic being admissible (never overestimates true remaining cost); subtle bugs if we optimize on time but use a distance-based heuristic without converting; no built-in reference implementation to cross-check against.

### Option C — Both: A* in production, Dijkstra as reference implementation
- **Pros:** best of both — A*'s speed where it matters, plus a Dijkstra baseline we can use for correctness cross-checks in tests ("A* and Dijkstra must return paths of equal cost on every fixture") and for benchmarking ("A* explores N nodes vs Dijkstra's M on the same input"); strong educational and interview value — I can explain *when* each wins and I have real numbers to back it up.
- **Cons:** two code paths to maintain; a small amount of duplicated logic (priority-queue iteration shape); a reader might wonder "why is Dijkstra here if we don't use it?" — answered by the docstring and this ADR.

## Decision

**Option C.** Implement both A* and Dijkstra as pure functions in `app/algorithms/`. The production `navigation_service` calls A*. The test suite runs a cross-check: every path returned by A* must have cost equal to the path returned by Dijkstra on the same input. A benchmark script (`scripts/bench_routing.py`) prints a comparison table of nodes-expanded and wall-time for each algorithm on fixture graphs.

## Why

1. **Correctness guarantee.** A* and Dijkstra are both optimal for non-negative weights (A* conditional on an admissible heuristic). Running them on the same fixtures and asserting equal-cost results gives us a strong correctness check that catches bugs *in the implementation* (not just the algorithm) — e.g., a wrong priority-queue tiebreak, a missed `closed-set` update, an off-by-one in path reconstruction.
2. **Honest performance claim.** With both implementations in the repo and a benchmark script, we can say *"A* explores 23% as many nodes as Dijkstra on a 2,000-node graph"* with a measurement, not a vibe.
3. **Interview depth.** Being asked "how does A* work?" is table stakes. Being asked "how do you know your A* is correct?" and answering "I run it against Dijkstra on every test fixture" is a differentiating answer.
4. **Low maintenance cost.** Both algorithms share the same graph API and are < 50 lines each. The duplication is small and intentional.

## Trade-offs

| We give up | We accept this because |
|---|---|
| Simplicity of a single algorithm module | We gain correctness cross-checks and a benchmark story. |
| A little compile/import surface area | Trivial. |
| Someone might run Dijkstra accidentally thinking it's A* | The service layer makes it explicit; module names (`astar.py`, `dijkstra.py`) are unambiguous. |

## Why A* is the production choice

A* with an admissible heuristic is **strictly ≥ as good as** Dijkstra: in the worst case it degrades to Dijkstra's behaviour, and in the typical case it explores far fewer nodes. We have perfect-fit heuristic data (Euclidean distance between nodes). There is no reason to pay Dijkstra's uniform exploration cost in production.

## Heuristic design (noted here, elaborated in Phase 2 planning)

- **Distance-cost mode:** `h(n) = euclidean(n, goal)`. Admissible by construction (straight-line is a lower bound on any path).
- **Time-cost mode:** `h(n) = euclidean(n, goal) / walking_speed_m_per_s`. Still admissible — it ignores the possibility of elevator wait time, which means it *underestimates* true remaining cost. Underestimates are fine; overestimates would break optimality.
- **Different-floor case:** if goal is on a different floor and we're on floor_a, we add `0` to the heuristic (the vertical "distance" has no horizontal component). Admissible but potentially loose, so A* explores a bit more. If this becomes a measurable cost, we can tighten it later.

## What would change this later

- **Graph grows to > 50,000 nodes:** reach for landmark-based heuristics (ALT) or contraction hierarchies. A* alone starts to feel sluggish.
- **Need k-shortest paths or all-pairs:** switch to Yen's or Johnson's algorithm; A* is single-source single-target.
- **Need to support negative edge weights** (unlikely in this domain): neither A* nor Dijkstra handles them; switch to Bellman-Ford.
- **Dijkstra becomes dead weight:** if the cross-check tests get flaky or slow enough to annoy, move Dijkstra out of the test suite into the benchmark script only.

## Related

- See [`../03-phase-2-routing.md`](../03-phase-2-routing.md) for the cost-function, profile, and API spec.
- See [009](009-astar-heuristic-strategy.md) for why `h` has no vertical term.
