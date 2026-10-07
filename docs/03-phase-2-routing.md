# 03 — Phase 2: Indoor routing

**Status:** Complete against portable PostgreSQL 16.15 (same instance as Phase 1). Phase 3 consumes this API from the SVG map.
**Date:** 2026-10-06.

This is the CS core of MallMind: turn the Phase 1 directed graph into shortest paths, with a Dijkstra oracle, an A* production router, accessibility as edge filters, deterministic instructions, and one HTTP endpoint.

---

## 1. How the database becomes a routing graph

Postgres stores the map. Algorithms never query it.

| DB | In-memory |
|---|---|
| `map_nodes.id, floor_id, x, y, node_type, location_id` | `GraphNode` plus `floor_level` joined from `floors` |
| `map_edges` (directed) | adjacency list `outgoing[from_id] → [GraphEdge, …]` |
| `locations.anchor_node` | `NavigationService` resolves Location → node id, then calls Dijkstra/A* |

`GraphRepository.load_mall_graph` builds a `MallGraph` per request. No cache. NOVA is 91 nodes / 248 directed edges; a cache would be premature (see §8).

Seed tests can skip the DB: `graph_from_seed(build_nova_mall())` uses the same topology with stable uuid5 ids.

### Adjacency list, not matrix

A mall graph is sparse: hallways are a 6×3 grid per floor plus a handful of spurs and four shafts. `E` is a few times `V` (248 / 91 ≈ 2.7).

| | Adjacency list | Adjacency matrix |
|---|---|---|
| Space | `O(V + E)` | `O(V²)` |
| Expand neighbours | `O(degree(u))` | `O(V)` |
| 91-node NOVA | ~340 slots | 8,281 slots |
| 100×100 grid | ~50k slots | 100 million slots |

Dijkstra/A* with a binary heap are `O((V + E) log V)` on a list. A matrix would pay `O(V)` per expansion even for degree-2 corridors. List wins on space and on the inner loop.

---

## 2. Dijkstra (correctness baseline)

`app/routing/dijkstra.py`. Own code, not NetworkX.

- Directed, positive weights (`distance_m` or `avg_seconds`).
- Binary heap (`heapq`) + closed set: the first time a node is closed, `g` is optimal.
- Reconstructs node ids, edge ids, total metres, total seconds, `nodes_expanded`.
- Failures: `unknown_node`, `no_path`. Same start/goal returns a one-node zero-cost route.

Complexity with our list: `O((V + E) log V)`.

Production does **not** call Dijkstra. Tests and `scripts/bench_routing.py` do.

---

## 3. A* (production)

`app/routing/astar.py` is a separate file. It shares only path reconstruction. That is intentional: a bug in the A* loop cannot "fix itself" by sharing Dijkstra's relaxation.

`f(n) = g(n) + h(n)`. With an admissible `h`, the first time the goal is closed, `g` is optimal — the same cost Dijkstra would report, usually with fewer expansions when `h` is informative.

The service layer calls A*.

---

## 4. Heuristic

See [ADR-009](decisions/009-astar-heuristic-strategy.md).

- **Admissible:** `h(n)` never exceeds true remaining cost. Straight-line metres cannot overestimate walking along edges whose lengths are at least the coordinate span. Ignoring elevator wait *underestimates* remaining time, which is allowed.
- **Consistent:** `h(u) ≤ w(u,v) + h(v)` on hallways (triangle inequality + edge length ≥ span). Elevator landings share `(x, y)`, so `h(u) = h(v)` and `w ≥ 0`.
- **Cross-floor:** no vertical bonus. A `min(elevator wait)` addend would be illegal if stairs or an escalator can beat that wait.
- **Time mode:** `h = euclidean / 1.25 m/s`, matching the seed's `WALK_MPS`.

Why A* can visit fewer nodes: Dijkstra's priority is `g` only, so it floods a disc (or diamond) around the start. A* prefers nodes with small `g + h`, i.e. that still look like they can beat the best known path to the goal. Nodes that are cheap to reach but point the wrong way get delayed or never closed.

---

## 5. Accessibility — filters, not forked algorithms

`app/routing/policy.py`:

| Profile | Predicate |
|---|---|
| `normal` | every edge |
| `wheelchair` | `edge.accessible` (stairs and escalators are `false` in the seed; elevators are `true`) |
| `avoid_stairs` | `edge.edge_type is not STAIRS` (escalators still allowed) |

Dijkstra and A* take `allow: EdgeFilter`. They never mention stairs. One algorithm, three policies, one place to test.

Escalator direction is **not** a policy. An `ESCALATOR_UP` row has no reverse row. Riding it down is impossible because there is nothing to expand. That is ADR-008 paying off.

---

## 6. Location-to-location vs algorithms

```
POST /api/v1/navigation/route
  → NavigationService          # Location UUIDs, names, HTTP errors
      → GraphRepository        # SQL → MallGraph
      → astar / dijkstra       # node ids only
      → instructions_for       # Walk Xm / elevator / stairs / escalator / Arrive at …
```

The algorithm layer has no SQLAlchemy imports. The service never implements shortest path. Tests can swap `algorithm="dijkstra"` to compare costs against the seed graph without going through HTTP.

---

## 7. HTTP API

`POST /api/v1/navigation/route`

Request:

```json
{
  "from_location_id": "<uuid>",
  "to_location_id": "<uuid>",
  "profile": "wheelchair",
  "cost_mode": "distance"
}
```

Success (200): `route` (node id strings), `distance_m`, `estimated_seconds`, `floors` in visit order, `instructions`, `algorithm: "astar"`, plus `nodes_expanded` for honesty.

Errors (`{"code","message"}`):

| Situation | HTTP | code |
|---|---|---|
| Unknown location UUID | 404 | `unknown_location` |
| Same start and destination | 400 | `same_location` |
| Location exists but has no anchor node | 422 | `missing_anchor` |
| No path (including wheelchair with only stairs) | 422 | `no_path` / `no_accessible_path` |
| Invalid `profile` / `cost_mode` enum | 422 | FastAPI/Pydantic validation |

404 vs 422: 404 means "this id is not a location." 422 means "the ids are well-formed but routing cannot produce a path" (or the location is not graph-connected). 400 is a client contradiction (same id twice). Invalid enums fail at the body parser so the service never sees a mystery string.

---

## 8. Benchmarks (measured 2026-10-06, this machine)

Script: `backend/scripts/bench_routing.py`. Means of `time.perf_counter` over `n` runs. Wall-clock is noisy on Windows (timer granularity, frequency scaling, GC, other processes). **`nodes_expanded` is deterministic** and is the comparison that matters.

Graph: NOVA Mall **seed topology** (91 nodes, 248 directed edges) — the same graph that was inserted into PostgreSQL. Synthetic grids are **not** in the production seed.

### NOVA Mall (`n = 200`)

| Route | Dijkstra cost | D expanded | D mean | A* cost | A* expanded | A* mean | A*/D exp. |
|---|---|---|---|---|---|---|---|
| Nike → Zara (short, same floor) | 44.0 m | 7 | 0.024 ms | 44.0 m | 4 | 0.023 ms | 0.571 |
| Parking entrance → Guest Services (long, same floor) | 182.0 m | 86 | 0.262 ms | 182.0 m | 46 | 0.171 ms | 0.535 |
| Main entrance → Muji (cross-floor) | 118.0 m | 70 | 0.231 ms | 118.0 m | 27 | 0.123 ms | 0.386 |
| Nike → Apple (cross-floor, **time**) | 137.0 s | 68 | 0.224 ms | 137.0 s | 30 | 0.118 ms | 0.441 |
| Restroom G-north → L1, wheelchair | 180.0 m | 83 | 0.272 ms | 180.0 m | 41 | 0.152 ms | 0.494 |
| Same pair, avoid-stairs | 180.0 m | 83 | 0.308 ms | 180.0 m | 41 | 0.160 ms | 0.494 |

On this mall, A* expanded **38–57%** as many nodes as Dijkstra at equal cost.

### Synthetic 4-connected grids, corner → opposite corner

| Grid | V / E | Cost | Expansions (both) | Dijkstra mean | A* mean |
|---|---|---|---|---|---|
| 20×20 | 400 / 1,520 | 380 m | **400 = 400** | 1.838 ms | 1.800 ms |
| 50×50 | 2,500 / 9,800 | 980 m | **2,500 = 2,500** | 16.976 ms | 12.864 ms |
| 100×100 | 10,000 / 39,600 | 1,980 m | **10,000 = 10,000** | 48.128 ms | 55.468 ms |

A* tracemalloc peak on one 100×100 run: **1374.4 KiB** of Python allocations (not RSS; not a process-wide memory figure).

**Why expansions tied:** start and goal are opposite corners of a filled rectangle. Every cell is inside that rectangle. Euclidean `f*` on a 4-connected grid never exceeds Manhattan `C*`, so A* cannot close the goal before it has closed every other cell. A* then *loses* on the 100×100 mean because it still computes `hypot` at every expansion.

That is not a failed implementation. It is the heuristic telling the truth. A* *does* prune on NOVA (sparse corridors) and on the unit-test "blob north of the start" graph. We did not invent a grid number that made A* look better.

No C++, Redis, or route cache. Python on NOVA is sub-millisecond. Optimization is not earned yet.

---

## 9. Tests

`pytest` on 2026-10-06 with `DATABASE_URL=postgresql+asyncpg://mallmind@127.0.0.1:5432/mallmind`:

**71 passed, 0 skipped.**

Coverage includes Dijkstra/A* agreement on all 31×31 NOVA location pairs (distance and time), wheelchair vs stairs, one-way escalators, Location → anchor → route, and `POST /api/v1/navigation/route` against the live seeded database.

---

## 10. What Phase 3 should not redo

Routing is done. Phase 3 is the map UI: draw floors, draw the polyline from `route` / `node_ids`, show instructions. Do not change the cost function to make the line "look nicer."
