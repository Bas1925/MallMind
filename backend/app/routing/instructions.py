"""Deterministic walking instructions from a routed edge list. No LLM."""

from __future__ import annotations

from app.models.enums import EdgeType
from app.routing.types import GraphEdge, MallGraph, RouteResult


def instructions_for(
    graph: MallGraph,
    result: RouteResult,
    *,
    destination_name: str | None = None,
) -> list[str]:
    if not result.ok:
        return []
    if len(result.node_ids) <= 1:
        dest = destination_name or "destination"
        return [f"Already at {dest}"]

    by_id = {e.id: e for edges in graph.outgoing.values() for e in edges}
    steps: list[str] = []
    hallway_run = 0.0
    for eid in result.edge_ids:
        edge = by_id[eid]
        if edge.edge_type is EdgeType.HALLWAY:
            hallway_run += edge.distance_m
            continue
        if hallway_run > 0:
            steps.append(f"Walk {hallway_run:.0f} m")
            hallway_run = 0.0
        steps.append(_vertical_line(graph, edge))
    if hallway_run > 0:
        steps.append(f"Walk {hallway_run:.0f} m")
    dest = destination_name
    if dest is None:
        last = graph.nodes[result.node_ids[-1]]
        dest = last.key.replace("loc-", "") if last.key else "destination"
    steps.append(f"Arrive at {dest}")
    return steps


def floors_on_route(graph: MallGraph, node_ids: tuple) -> list[int]:
    seen: list[int] = []
    for nid in node_ids:
        level = graph.nodes[nid].floor_level
        if not seen or seen[-1] != level:
            seen.append(level)
    return seen


def _vertical_line(graph: MallGraph, edge: GraphEdge) -> str:
    src = graph.nodes[edge.from_id]
    dst = graph.nodes[edge.to_id]
    dest_floor = dst.floor_level
    if edge.edge_type is EdgeType.ELEVATOR:
        return f"Take the elevator to floor {dest_floor}"
    if edge.edge_type is EdgeType.STAIRS:
        return f"Take the stairs to floor {dest_floor}"
    if edge.edge_type is EdgeType.ESCALATOR_UP:
        return f"Use the escalator up to floor {dest_floor}"
    if edge.edge_type is EdgeType.ESCALATOR_DOWN:
        return f"Use the escalator down to floor {dest_floor}"
    return f"Continue to floor {dest_floor} from {src.floor_level}"
