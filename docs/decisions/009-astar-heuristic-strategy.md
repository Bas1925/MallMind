# 009 — Euclidean A* heuristic with no vertical bonus

**Status:** Accepted
**Date:** 2026-10-06
**Deciders:** Basel

## Context

A* is the production router. Its optimality proof requires an admissible heuristic: `h(n) ≤ true remaining cost`. We have floor-local `(x, y)` from ADR-007 and two cost modes (metres vs seconds). The tempting extra is a "you must pay an elevator" term when `n` and the goal are on different floors.

## Options considered

### Option A — Euclidean in the plane, zero extra across floors
- **Pros:** admissible for both cost modes; consistent on hallways whose `distance_m` is at least the coordinate span; one function; cannot secretly overestimate a cheap stairs route.
- **Cons:** loose on cross-floor queries, so A* expands more nodes than a tighter bound would.

### Option B — Euclidean plus `min(elevator wait)` when floors differ
- **Pros:** tighter on elevator-heavy malls.
- **Cons:** not admissible if a stairs (or escalator) path is cheaper than that wait. Our seed's stairs are 40 s and elevators 25 s, but a future mall can invert that. A "clever" bonus that is wrong on one fixture silently ships a suboptimal router.

### Option C — Different heuristics per profile (wheelchair gets the elevator bonus, normal does not)
- **Pros:** could be tight *and* admissible if each profile's remaining graph really cannot beat the bonus.
- **Cons:** three heuristics to keep in lockstep with `policy.py`; a profile change becomes an algorithm change, which is the coupling we refused in Phase 2.

## Decision

**Option A.** `h = hypot(Δx, Δy)` in distance mode, and `h / 1.25 m/s` in time mode. No vertical addend. Profiles stay in the edge filter, not in `h`.

## Why

1. **Correctness first.** Underestimates preserve optimality. Overestimates do not. Zero is the vertical term we can defend without enumerating every shaft type.
2. **The production graph is sparse corridors, not a filled rectangle.** Benchmarks on NOVA Mall (91 nodes) showed A* expanding 39–57% as many nodes as Dijkstra. That is enough of a win to ship A* without tightening `h`.
3. **Open-grid measurements warned us not to worship the heuristic.** On a 4-connected `N×N` grid, corner to opposite corner, A* expanded *every* node — the same count as Dijkstra. Every cell lies in the start–goal bounding box, and Euclidean `f*` never exceeds Manhattan `C*`, so nothing is pruned. On the 100×100 grid A* was *slower* (55.5 ms vs 48.1 ms mean) because it paid `hypot` for no fewer expansions. That is a reason to keep Dijkstra as an oracle, not a reason to "fix" `h` with an unsafe bonus.

## Trade-offs

| We give up | We accept this because |
|---|---|
| Tighter cross-floor `h` | One wrong bonus would make A* disagree with Dijkstra on a fixture we already cross-check. |
| Profile-specific heuristics | Accessibility is an edge predicate. Mixing it into `h` duplicates policy. |

## What would change this later

- A measured NOVA-scale regression where cross-floor A* expansions approach Dijkstra's *and* we can prove a vertical lower bound that no legal profile can beat (for example: every cross-floor path uses an elevator whose wait is ≥ `W`). Then a `+ W` term becomes admissible for that profile only.
- Landmark / ALT heuristics if a single mall exceeds tens of thousands of nodes.

## Related

- [`002-astar-with-dijkstra-baseline.md`](002-astar-with-dijkstra-baseline.md)
- [`007-floor-local-coordinates.md`](007-floor-local-coordinates.md)
- [`../03-phase-2-routing.md`](../03-phase-2-routing.md)
