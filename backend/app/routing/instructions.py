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
    # A shaft ride Ground -> L1 -> L2 is two edges but one thing to do:
    # stay in the elevator. Consecutive vertical edges of one type merge.
    ride: GraphEdge | None = None
    for eid in result.edge_ids:
        edge = by_id[eid]
        if ride is not None and edge.edge_type is not ride.edge_type:
            steps.append(_vertical_line(graph, ride))
            ride = None
        if edge.edge_type is EdgeType.HALLWAY:
            hallway_run += edge.distance_m
            continue
        if hallway_run > 0:
            steps.append(f"Walk {hallway_run:.0f} m")
            hallway_run = 0.0
        ride = edge
    if ride is not None:
        steps.append(_vertical_line(graph, ride))
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


def floor_label(graph: MallGraph, level: int) -> str:
    return graph.floor_names.get(level, f"floor {level}")


def _vertical_line(graph: MallGraph, edge: GraphEdge) -> str:
    """Describe a ride by where it ends. `edge` is the last edge of the ride."""
    src = graph.nodes[edge.from_id]
    dest = floor_label(graph, graph.nodes[edge.to_id].floor_level)
    if edge.edge_type is EdgeType.ELEVATOR:
        return f"Take the elevator to {dest}"
    if edge.edge_type is EdgeType.STAIRS:
        return f"Take the stairs to {dest}"
    if edge.edge_type is EdgeType.ESCALATOR_UP:
        return f"Use the escalator up to {dest}"
    if edge.edge_type is EdgeType.ESCALATOR_DOWN:
        return f"Use the escalator down to {dest}"
    return f"Continue to {dest} from {floor_label(graph, src.floor_level)}"
