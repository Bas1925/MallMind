"""Dijkstra shortest path — correctness baseline.

Adjacency-list + binary heap: O((V + E) log V) with heapq.
Positive weights only (our CHECK constraints guarantee that).
"""

from __future__ import annotations

import heapq
import uuid
from dataclasses import replace

from app.routing.policy import EdgeFilter, allow_all, edge_cost
from app.routing.types import CostMode, GraphEdge, MallGraph, RouteResult


def dijkstra(
    graph: MallGraph,
    start: uuid.UUID,
    goal: uuid.UUID,
    *,
    cost_mode: CostMode = CostMode.DISTANCE,
    allow: EdgeFilter = allow_all,
) -> RouteResult:
    algo = "dijkstra"
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

    dist: dict[uuid.UUID, float] = {start: 0.0}
    prev_edge: dict[uuid.UUID, GraphEdge] = {}
    expanded = 0
    order: list[uuid.UUID] = []
    heap: list[tuple[float, int, uuid.UUID]] = []
    seq = 0
    heapq.heappush(heap, (0.0, seq, start))
    closed: set[uuid.UUID] = set()

    while heap:
        cost_so_far, _, current = heapq.heappop(heap)
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
        if cost_so_far > dist.get(current, float("inf")):
            continue
        for edge in graph.neighbors(current):
            if not allow(edge):
                continue
            nxt = edge.to_id
            if nxt not in graph.nodes:
                continue
            tentative = cost_so_far + edge_cost(edge, cost_mode)
            if tentative < dist.get(nxt, float("inf")):
                dist[nxt] = tentative
                prev_edge[nxt] = edge
                seq += 1
                heapq.heappush(heap, (tentative, seq, nxt))

    return RouteResult.fail(algo, "no_path", nodes_expanded=expanded, visited_ids=tuple(order))


def _reconstruct(
    graph: MallGraph,
    start: uuid.UUID,
    goal: uuid.UUID,
    prev_edge: dict[uuid.UUID, GraphEdge],
    algorithm: str,
    expanded: int,
) -> RouteResult:
    nodes = [goal]
    edges = []
    cur = goal
    while cur != start:
        edge = prev_edge[cur]
        edges.append(edge)
        cur = edge.from_id
        nodes.append(cur)
    nodes.reverse()
    edges.reverse()
    return RouteResult(
        ok=True,
        algorithm=algorithm,
        node_ids=tuple(n for n in nodes),
        edge_ids=tuple(e.id for e in edges),
        total_distance_m=sum(e.distance_m for e in edges),
        total_seconds=sum(e.avg_seconds for e in edges),
        nodes_expanded=expanded,
    )
