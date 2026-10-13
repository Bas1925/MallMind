"""Unweighted BFS and DFS path search.

A* and Dijkstra minimise a cost. These two do not.

BFS expands one hop at a time, so the first time it reaches the goal the
path has the fewest hallways. That path can still be a long walk.

DFS follows one hallway as far as it can, then backtracks. Neighbor order
is fixed: farther east, then farther north. The service maze is drawn so
that order enters the long corridor and its dead ends before the short one.
The first path DFS finds is therefore longer than the BFS path.
"""

from __future__ import annotations

import uuid
from collections import deque
from dataclasses import replace

from app.routing.dijkstra import _reconstruct
from app.routing.policy import EdgeFilter, allow_all
from app.routing.types import GraphEdge, MallGraph, RouteResult


def bfs(
    graph: MallGraph,
    start: uuid.UUID,
    goal: uuid.UUID,
    *,
    allow: EdgeFilter = allow_all,
) -> RouteResult:
    return _search(graph, start, goal, allow=allow, mode="bfs")


def dfs(
    graph: MallGraph,
    start: uuid.UUID,
    goal: uuid.UUID,
    *,
    allow: EdgeFilter = allow_all,
) -> RouteResult:
    return _search(graph, start, goal, allow=allow, mode="dfs")


def _search(
    graph: MallGraph,
    start: uuid.UUID,
    goal: uuid.UUID,
    *,
    allow: EdgeFilter,
    mode: str,
) -> RouteResult:
    if start not in graph.nodes or goal not in graph.nodes:
        return RouteResult.fail(mode, "unknown_node")
    if start == goal:
        return RouteResult(
            ok=True,
            algorithm=mode,
            node_ids=(start,),
            edge_ids=(),
            total_distance_m=0.0,
            total_seconds=0.0,
            nodes_expanded=1,
            visited_ids=(start,),
        )

    prev_edge: dict[uuid.UUID, GraphEdge] = {}
    seen = {start}
    order: list[uuid.UUID] = []
    pending: deque[uuid.UUID] = deque([start])

    while pending:
        current = pending.popleft() if mode == "bfs" else pending.pop()
        order.append(current)
        if current == goal:
            found = _reconstruct(graph, start, goal, prev_edge, mode, len(order))
            return replace(found, visited_ids=tuple(order))
        edges = _candidates(graph, current, allow, mode)
        if mode == "dfs":
            edges = list(reversed(edges))
        for edge in edges:
            nxt = edge.to_id
            if nxt in seen:
                continue
            seen.add(nxt)
            prev_edge[nxt] = edge
            pending.append(nxt)

    return RouteResult.fail(mode, "no_path", nodes_expanded=len(order), visited_ids=tuple(order))


def _candidates(
    graph: MallGraph, node_id: uuid.UUID, allow: EdgeFilter, mode: str
) -> list[GraphEdge]:
    edges = [edge for edge in graph.neighbors(node_id) if allow(edge) and edge.to_id in graph.nodes]
    if mode == "dfs":
        edges.sort(key=lambda edge: _east_then_north(graph, edge.to_id))
    return edges


def _east_then_north(graph: MallGraph, node_id: uuid.UUID) -> tuple[float, float, str]:
    node = graph.nodes[node_id]
    return (-node.x, -node.y, str(node_id))
