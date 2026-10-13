"""A* shortest path. Separate from Dijkstra; same RouteResult shape.

f(n) = g(n) + h(n). h is admissible (see heuristic.py), so the first time
the goal is closed the g-score is optimal — same cost as Dijkstra, typically
fewer expansions when the heuristic is informative.
"""

from __future__ import annotations

import heapq
import uuid
from dataclasses import replace

from app.routing.dijkstra import _reconstruct
from app.routing.heuristic import heuristic
from app.routing.policy import EdgeFilter, allow_all, edge_cost
from app.routing.types import CostMode, GraphEdge, MallGraph, RouteResult


def astar(
    graph: MallGraph,
    start: uuid.UUID,
    goal: uuid.UUID,
    *,
    cost_mode: CostMode = CostMode.DISTANCE,
    allow: EdgeFilter = allow_all,
) -> RouteResult:
    algo = "astar"
    if start not in graph.nodes or goal not in graph.nodes:
        return RouteResult.fail(algo, "unknown_node")
    if start == goal:
        return RouteResult(
            ok=True,
            algorithm=algo,
            node_ids=(start,),
            edge_ids=(),
            total_distance_m=0.0,
            total_seconds=0.0,
            nodes_expanded=1,
        )

    goal_node = graph.nodes[goal]
    g: dict[uuid.UUID, float] = {start: 0.0}
    prev_edge: dict[uuid.UUID, GraphEdge] = {}
    expanded = 0
    order: list[uuid.UUID] = []
    seq = 0
    start_h = heuristic(graph.nodes[start], goal_node, cost_mode)
    heap: list[tuple[float, int, uuid.UUID]] = [(start_h, seq, start)]
    closed: set[uuid.UUID] = set()

    while heap:
        _f, _, current = heapq.heappop(heap)
        if current in closed:
            continue
        closed.add(current)
        order.append(current)
        expanded += 1
        if current == goal:
            return replace(
                _reconstruct(graph, start, goal, prev_edge, algo, expanded),
                visited_ids=tuple(order),
            )
        g_current = g[current]
        for edge in graph.neighbors(current):
            if not allow(edge):
                continue
            nxt = edge.to_id
            if nxt not in graph.nodes or nxt in closed:
                continue
            tentative = g_current + edge_cost(edge, cost_mode)
            if tentative < g.get(nxt, float("inf")):
                g[nxt] = tentative
                prev_edge[nxt] = edge
                seq += 1
                h = heuristic(graph.nodes[nxt], goal_node, cost_mode)
                heapq.heappush(heap, (tentative + h, seq, nxt))

    return RouteResult.fail(algo, "no_path", nodes_expanded=expanded, visited_ids=tuple(order))
