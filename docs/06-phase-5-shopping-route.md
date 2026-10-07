# 06 — Phase 5: Multi-stop shopping routes

**Status:** Implemented on portable PostgreSQL 16.15. Numbers below are from `python scripts/bench_tour.py` and a profile probe on 2026-10-06. This is an open tour with a measured heuristic gap. It is not a claim that TSP is solved.

## 1. This is not A*

A* answers one question: the cheapest path from A to B on the mall graph.

A shopping list is a different question. The start is fixed. The stops all have to be visited. The order is what we choose. The shopper does not have to walk back to the entrance.

That is an **open** tour. Classic TSP usually returns to the start. MallMind does not add that return leg.

With the start fixed, the number of orders is the factorial of the stop count:

| Stops | Orders (`k!`) |
|---|---|
| 3 | 6 |
| 5 | 120 |
| 10 | 3,628,800 |
| 20 | 2.43 × 10^18 |

Ten stops is already millions of orders. Twenty is not something you enumerate inside a request. A production planner needs a heuristic for the large cases and an exact solver for the small ones, and it needs to say which one it used.

## 2. Three jobs, not one new pathfinder

| Piece | Job |
|---|---|
| A* (`app/routing/astar.py`) | Shortest path between two anchors, under one profile |
| Tour optimizer (`app/routing/tour.py`) | Best order, given only a cost matrix |
| `TourService` | Build the matrix, pick a solver, stitch the A* segments |

The optimizer never sees hallways. For one request with a start plus `k` stops there are `n = k + 1` locations and `n × (n - 1)` directed pairs. Five stops means 30 A* calls. Twenty means 420. Those results live in two matrices (metres and seconds) for that request only. There is no Redis.

The objective is whichever `cost_mode` the client sent. The other metric is still reported, from the same order.

## 3. Baseline

The submitted order is scored on the same matrix. It is the unoptimized route, not a bad route. If nothing is shorter by more than a centimetre (`EPS = 0.01` m), the response keeps that order, sets `improved` to false, and says `No shorter route was found.` Time mode says `No faster route was found.` A zero-gain reshuffle is not shown as a win.

## 4. Nearest Neighbor

From the current location, take the cheapest unused stop. Repeat. Ties take the lowest index, so the same matrix always yields the same tour. Time is `O(k^2)` matrix lookups.

It does not guarantee the best order. A cheap first step can trap the rest of the walk. On this fixture the greedy tour costs 102 and the optimum costs 4:

```text
     1    2    3
0    1    2   10
1    0  100  100
2    1    0    1
3    1    1    0
```

Nearest Neighbor walks `0 → 1 → 2 → 3` because the first edge costs 1. The best open tour is `0 → 2 → 3 → 1`.

## 5. Nearest Neighbor + 2-opt

2-opt takes that greedy tour and reverses internal segments while the reversal is strictly cheaper. The start stays fixed. An accepted move cannot increase the cost. The search stops at a local optimum of that neighbourhood, or after `n²` moves.

It is not a global optimum. On the fixture above, after the directed-edge fix, 2-opt does reach cost 4 in 2 moves. On the real NOVA example in §7 it makes **0** moves and stays 4 m above Held-Karp.

The first 2-opt used the symmetric formula (replace only the two edges that touch the reversed span). Mall edges are directed. Reversing a span also reverses the edges inside it. Escalators are one way. That formula both missed a real improvement and "improved" a tour that was already optimal. The debugging note is `docs/debugging/2026-10-06-directed-2opt.md`.

## 6. Exact solver: Held-Karp, and only while it is cheap

Brute force is in the tests (`brute_force_open`) so the DP can be checked. It is not what the API runs.

Held-Karp for an open tour, start fixed:

- State `dp[mask][j]`: cheapest way to visit the stops in `mask`, ending at stop `j`.
- Base: `dp[{j}][j] = cost[start][j]`.
- Recurrence: `dp[mask][j] = min over i in mask, i ≠ j, of dp[mask without j][i] + cost[i][j]`.
- Time `O(2^k · k^2)`. Space `O(2^k · k)`. `k` is the stop count, not counting the start.

`scripts/bench_tour.py` on CPython 3.12, random directed matrices, 2026-10-06:

| Stops | Held-Karp |
|---|---|
| 8 | 2.41 ms |
| 10 | 17.13 ms |
| 12 | 89.30 ms |
| 14 | 543.22 ms |

**Exact solver for 1–12 stops. Heuristic from 13.** Twelve stays inside one click. Fourteen does not. The API also rejects more than **20** stops (`too_many_stops`, 400). Twenty is a shopping list, and the heuristic request at that size averaged 118 ms (§8). Ten thousand stops is not a product.

## 7. One real mall, one list

Profile `normal`, objective distance. Start Main Entrance. Submitted order Nike, Zara, Apple, ATM (Ground), Super-Pharm.

| Solver | Distance | Versus exact |
|---|---|---|
| Submitted order | 442.5 m | |
| Nearest Neighbor | 386.5 m | +1.0% |
| Nearest Neighbor + 2-opt | 386.5 m, 0 moves | +1.0% |
| Held-Karp | 382.5 m | optimum |

Chosen order: Main Entrance → ATM (Ground) → Apple → Zara → Nike → Super-Pharm.

Saved against the submitted order: **60.0 m, 13.6%, 48 s**. Algorithm reported: `held_karp`, because the exact cost matched the chosen tour. A* calls: 30.

2-opt did not move. The exact solver saved another 4 m. That is the gap we are willing to show.

## 8. Sampled NOVA Mall

Eight samples per size, `random.Random(0)`, start Main Entrance, profile normal, objective distance. Means. Exact column is blank when the cutoff skips Held-Karp. Gap percents are the mean of the per-sample gaps, not the gap of the means.

| Stops | Samples | A* calls | Mean ms | User m | NN m | 2-opt m | Exact m | NN gap | 2-opt gap |
|---|---|---|---|---|---|---|---|---|---|
| 3 | 8 | 12 | 25.1 | 290 | 258 | 256 | 254 | 1.5% | 0.6% |
| 5 | 8 | 30 | 30.4 | 522 | 426 | 420 | 399 | 7.1% | 5.3% |
| 7 | 8 | 56 | 42.5 | 731 | 613 | 573 | 559 | 10.5% | 2.4% |
| 10 | 8 | 110 | 62.8 | 1023 | 728 | 673 | 664 | 9.2% | 1.4% |
| 12 | 8 | 156 | 176.4 | 1322 | 807 | 770 | 734 | 9.8% | 4.8% |
| 15 | 8 | 240 | 80.7 | 1507 | 958 | 905 | | | |
| 20 | 8 | 420 | 118.1 | 2043 | 1186 | 1088 | | | |

At 7 stops, 2-opt cuts the mean gap from 10.5% to 2.4%. At 12 stops the mean request is 176 ms because Held-Karp is still on; the synthetic DP alone was 89 ms. At 15 and 20 the exact solver is off and the heuristic request stays near 80–118 ms. A* is most of that time.

The 2-opt gap is not monotone. At 12 stops the mean gap is 4.8%, worse than 1.4% at 10. Eight samples. That is the measurement, not a smoothed curve.

## 9. Profiles change the matrix

Pairwise costs are computed with `filter_for(profile)` before any ordering. We do not optimize on standard metres and then redraw a wheelchair path.

Same three locations, Restroom Ground North plus Restroom Level 1 and Nike. Order did not change. Metres did.

| Pair | Normal | Wheelchair |
|---|---|---|
| Restroom Ground North → Restroom Level 1 | 112.0 m | 180.0 m |
| Restroom Level 1 → Nike | 132.0 m | 160.0 m |
| Restroom Ground North → Nike | 44.0 m | 44.0 m |
| Optimized tour | 176.0 m | 204.0 m |

A different list does change the order. From Main Entrance, visiting Muji, Pages Bookstore, and H&M:

- Normal: Entrance → Muji → Pages → H&M, **298.0 m**
- Wheelchair: Entrance → H&M → Muji → Pages, **306.0 m**

The canonical five-store list happened to have the same matrix under `normal`, `wheelchair`, and `avoid_stairs` (382.5 m). Profile changes are real. They are not guaranteed on every list.

## 10. Unreachable stops

If any selected stop has no finite path from the start under that profile, the whole plan fails. Nothing is dropped.

Wheelchair, and the only edge is stairs with `accessible=false`:

```text
422 unreachable_stop
"No wheelchair-accessible route exists to Island B."
location_ids: ["…"]
```

Other profiles: `No route exists to {names} under profile {profile}.` A reachable graph with no Hamiltonian path is `no_tour`, also 422.

## 11. API

`POST /api/v1/navigation/optimize`

`profile: "standard"` is accepted and stored as `normal`. Empty list, duplicates (including the start), unknown ids, more than 20 stops, and a bad profile name are rejected before a tour is built. Distances are rounded to 0.1 m. Savings percents are rounded to 0.1.

The Plan tab sends this request, shows original versus optimized, and says so when nothing was saved. Details (algorithm, A* count, 2-opt moves, nearest-neighbor and exact distances, the pairwise matrix) are behind a toggle. Start route draws `node_ids` on the existing SVG. Stop numbers are on the markers for the floor you are looking at. Other floors keep their own numbers when you switch. There is no second map.

## 12. What this phase did not do

No fixed final stop (Parking Entrance B as a required end). No Redis. No new pathfinder. No auth, parking, Kafka, or Kubernetes. No extra model feature.
