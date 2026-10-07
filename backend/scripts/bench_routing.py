"""Real Dijkstra vs A* timings. Prints measurements; does not invent numbers.

Run from backend/:

    python scripts/bench_routing.py
"""

from __future__ import annotations

import statistics
import time
import tracemalloc
import uuid
from collections.abc import Callable

from app.routing.astar import astar
from app.routing.dijkstra import dijkstra
from app.routing.graph import graph_from_seed
from app.routing.policy import filter_for
from app.routing.synthetic import grid_graph
from app.routing.types import CostMode, MallGraph, RouteProfile
from app.seed.nova_mall import build_nova_mall

REPEAT_NOVA = 200
REPEAT_GRID = {20: 80, 50: 20, 100: 8}


def _mean_seconds(fn: Callable[[], object], repeats: int) -> float:
    samples = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - t0)
    return statistics.mean(samples)


def _run_pair(
    graph: MallGraph,
    start: uuid.UUID,
    goal: uuid.UUID,
    *,
    profile: RouteProfile = RouteProfile.NORMAL,
    cost_mode: CostMode = CostMode.DISTANCE,
    repeats: int,
) -> None:
    allow = filter_for(profile)
    d = dijkstra(graph, start, goal, cost_mode=cost_mode, allow=allow)
    a = astar(graph, start, goal, cost_mode=cost_mode, allow=allow)
    d_t = _mean_seconds(
        lambda: dijkstra(graph, start, goal, cost_mode=cost_mode, allow=allow), repeats
    )
    a_t = _mean_seconds(
        lambda: astar(graph, start, goal, cost_mode=cost_mode, allow=allow), repeats
    )
    d_cost = d.total_distance_m if cost_mode is CostMode.DISTANCE else d.total_seconds
    a_cost = a.total_distance_m if cost_mode is CostMode.DISTANCE else a.total_seconds
    print(
        f"  Dijkstra  ok={d.ok}  cost={d_cost:.4f}  expanded={d.nodes_expanded}  "
        f"mean={d_t * 1000:.3f} ms  (n={repeats})"
    )
    print(
        f"  A*        ok={a.ok}  cost={a_cost:.4f}  expanded={a.nodes_expanded}  "
        f"mean={a_t * 1000:.3f} ms  (n={repeats})"
    )
    if d.ok and a.ok:
        ratio = a.nodes_expanded / d.nodes_expanded if d.nodes_expanded else 1.0
        print(f"  A*/Dijkstra expansions: {ratio:.3f}")


def bench_nova() -> None:
    graph = graph_from_seed(build_nova_mall())
    print(
        f"NOVA Mall seed graph: V={len(graph.nodes)} "
        f"E={sum(len(v) for v in graph.outgoing.values())}"
    )
    cases = [
        ("short same-floor", "loc-nike", "loc-zara", RouteProfile.NORMAL, CostMode.DISTANCE),
        (
            "long same-floor",
            "loc-parking-entrance",
            "loc-guest-services",
            RouteProfile.NORMAL,
            CostMode.DISTANCE,
        ),
        ("cross-floor", "loc-main-entrance", "loc-muji", RouteProfile.NORMAL, CostMode.DISTANCE),
        ("cross-floor time", "loc-nike", "loc-apple", RouteProfile.NORMAL, CostMode.TIME),
        (
            "wheelchair cross-floor",
            "loc-restroom-g-north",
            "loc-restroom-l1",
            RouteProfile.WHEELCHAIR,
            CostMode.DISTANCE,
        ),
        (
            "avoid-stairs cross-floor",
            "loc-restroom-g-north",
            "loc-restroom-l1",
            RouteProfile.AVOID_STAIRS,
            CostMode.DISTANCE,
        ),
    ]
    for title, src, dst, profile, mode in cases:
        print(f"\nRoute: {title}  ({src} -> {dst}, profile={profile.value}, mode={mode.value})")
        _run_pair(
            graph,
            graph.node_by_key(src).id,
            graph.node_by_key(dst).id,
            profile=profile,
            cost_mode=mode,
            repeats=REPEAT_NOVA,
        )


def bench_grids() -> None:
    ns = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    print("\n=== Synthetic 4-connected grids (not in production seed) ===")
    for n in (20, 50, 100):
        graph = grid_graph(n, n)
        start = uuid.uuid5(ns, "0,0")
        goal = uuid.uuid5(ns, f"{n - 1},{n - 1}")
        v = len(graph.nodes)
        e = sum(len(x) for x in graph.outgoing.values())
        print(f"\nGrid {n}x{n}: V={v} E={e}  corner -> opposite corner")
        if n == 100:
            tracemalloc.start()
            astar(graph, start, goal)
            _current, peak = tracemalloc.get_traced_memory()
            del _current
            tracemalloc.stop()
            print(
                f"  A* tracemalloc peak: {peak / 1024:.1f} KiB (Python allocations during one run)"
            )
        _run_pair(graph, start, goal, repeats=REPEAT_GRID[n])


def main() -> None:
    print("MallMind routing benchmark")
    print("Wall-clock means are noisy on Windows (timer resolution, turbo, GC).")
    print("nodes_expanded is deterministic and is the comparison that matters.\n")
    bench_nova()
    bench_grids()


if __name__ == "__main__":
    main()
