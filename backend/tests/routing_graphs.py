"""Tiny graphs for algorithm tests. Not production seed data."""

from __future__ import annotations

import uuid

from app.models.enums import EdgeType, NodeType
from app.routing.types import GraphEdge, GraphNode, MallGraph

_NS = uuid.UUID("11111111-2222-3333-4444-555555555555")


def nid(key: str) -> uuid.UUID:
    return uuid.uuid5(_NS, f"n:{key}")


def eid(a: str, b: str) -> uuid.UUID:
    return uuid.uuid5(_NS, f"e:{a}->{b}")


def node(
    key: str,
    *,
    x: float,
    y: float,
    floor_level: int = 0,
    node_type: NodeType = NodeType.HALLWAY_JUNCTION,
    location_id: uuid.UUID | None = None,
) -> GraphNode:
    return GraphNode(
        id=nid(key),
        floor_id=uuid.uuid5(_NS, f"floor:{floor_level}"),
        floor_level=floor_level,
        x=x,
        y=y,
        node_type=node_type,
        location_id=location_id,
        key=key,
    )


def edge(
    a: str,
    b: str,
    *,
    distance_m: float,
    avg_seconds: float | None = None,
    accessible: bool = True,
    edge_type: EdgeType = EdgeType.HALLWAY,
) -> GraphEdge:
    seconds = distance_m / 1.25 if avg_seconds is None else avg_seconds
    return GraphEdge(
        id=eid(a, b),
        from_id=nid(a),
        to_id=nid(b),
        distance_m=distance_m,
        avg_seconds=seconds,
        accessible=accessible,
        edge_type=edge_type,
    )


def mall_graph(nodes: list[GraphNode], edges: list[GraphEdge]) -> MallGraph:
    by_key = {n.key: n.id for n in nodes if n.key}
    outgoing: dict[uuid.UUID, list[GraphEdge]] = {n.id: [] for n in nodes}
    for e in edges:
        outgoing[e.from_id].append(e)
    by_location_id = {n.location_id: n.id for n in nodes if n.location_id is not None}
    return MallGraph(
        nodes={n.id: n for n in nodes},
        outgoing=outgoing,
        by_key=by_key,
        by_location_id=by_location_id,
    )


def directed_two_node() -> MallGraph:
    """A → B only. Used to prove directed traversal."""
    return mall_graph(
        [node("a", x=0, y=0), node("b", x=10, y=0)],
        [edge("a", "b", distance_m=10)],
    )


def weighted_triangle() -> MallGraph:
    """Cheap A-C via B (2+2) vs expensive direct A-C (100)."""
    return mall_graph(
        [node("a", x=0, y=0), node("b", x=2, y=0), node("c", x=4, y=0)],
        [
            edge("a", "b", distance_m=2),
            edge("b", "c", distance_m=2),
            edge("a", "c", distance_m=100),
            edge("c", "b", distance_m=2),
            edge("b", "a", distance_m=2),
            edge("c", "a", distance_m=100),
        ],
    )


def disconnected() -> MallGraph:
    return mall_graph(
        [node("a", x=0, y=0), node("b", x=10, y=0), node("c", x=100, y=100)],
        [edge("a", "b", distance_m=10), edge("b", "a", distance_m=10)],
    )


def two_floor_vertical(*, stairs_only: bool = False) -> MallGraph:
    """Ground A and upper B, plus a shaft.

    If stairs_only, the only vertical connector is inaccessible stairs.
    Otherwise both stairs (short, inaccessible) and elevator (longer walk, accessible).
    """
    nodes = [
        node("g-west", x=0, y=0, floor_level=0),
        node("g-east", x=40, y=0, floor_level=0),
        node("u-west", x=0, y=0, floor_level=1),
        node("u-east", x=40, y=0, floor_level=1),
        node("stairs-g", x=0, y=0, floor_level=0, node_type=NodeType.STAIRS_LANDING),
        node("stairs-u", x=0, y=0, floor_level=1, node_type=NodeType.STAIRS_LANDING),
    ]
    edges = [
        edge("g-west", "stairs-g", distance_m=1),
        edge("stairs-g", "g-west", distance_m=1),
        edge("u-west", "stairs-u", distance_m=1),
        edge("stairs-u", "u-west", distance_m=1),
        edge(
            "stairs-g",
            "stairs-u",
            distance_m=8,
            avg_seconds=30,
            accessible=False,
            edge_type=EdgeType.STAIRS,
        ),
        edge(
            "stairs-u",
            "stairs-g",
            distance_m=8,
            avg_seconds=30,
            accessible=False,
            edge_type=EdgeType.STAIRS,
        ),
    ]
    if not stairs_only:
        nodes.extend(
            [
                node("elev-g", x=40, y=0, floor_level=0, node_type=NodeType.ELEVATOR_LANDING),
                node("elev-u", x=40, y=0, floor_level=1, node_type=NodeType.ELEVATOR_LANDING),
            ]
        )
        edges.extend(
            [
                edge("g-west", "g-east", distance_m=40),
                edge("g-east", "g-west", distance_m=40),
                edge("u-west", "u-east", distance_m=40),
                edge("u-east", "u-west", distance_m=40),
                edge("g-east", "elev-g", distance_m=1),
                edge("elev-g", "g-east", distance_m=1),
                edge("u-east", "elev-u", distance_m=1),
                edge("elev-u", "u-east", distance_m=1),
                edge(
                    "elev-g",
                    "elev-u",
                    distance_m=0,
                    avg_seconds=25,
                    accessible=True,
                    edge_type=EdgeType.ELEVATOR,
                ),
                edge(
                    "elev-u",
                    "elev-g",
                    distance_m=0,
                    avg_seconds=25,
                    accessible=True,
                    edge_type=EdgeType.ELEVATOR,
                ),
            ]
        )
    return mall_graph(nodes, edges)


def escalator_pair() -> MallGraph:
    """Up-only and down-only shafts; no hallway connecting the landings across floors."""
    return mall_graph(
        [
            node("up-g", x=0, y=0, floor_level=0, node_type=NodeType.ESCALATOR_UP_LANDING),
            node("up-u", x=0, y=0, floor_level=1, node_type=NodeType.ESCALATOR_UP_LANDING),
            node("dn-g", x=10, y=0, floor_level=0, node_type=NodeType.ESCALATOR_DOWN_LANDING),
            node("dn-u", x=10, y=0, floor_level=1, node_type=NodeType.ESCALATOR_DOWN_LANDING),
        ],
        [
            edge(
                "up-g",
                "up-u",
                distance_m=8,
                avg_seconds=20,
                accessible=False,
                edge_type=EdgeType.ESCALATOR_UP,
            ),
            edge(
                "dn-u",
                "dn-g",
                distance_m=8,
                avg_seconds=18,
                accessible=False,
                edge_type=EdgeType.ESCALATOR_DOWN,
            ),
        ],
    )


def path_edge_types(graph: MallGraph, edge_ids: tuple[uuid.UUID, ...]) -> list[EdgeType]:
    by_id = {e.id: e for edges in graph.outgoing.values() for e in edges}
    return [by_id[eid_].edge_type for eid_ in edge_ids]
