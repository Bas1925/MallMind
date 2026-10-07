"""Synthetic grid graphs for algorithm scaling benchmarks. Not production seed."""

from __future__ import annotations

import uuid

from app.models.enums import EdgeType, NodeType
from app.routing.constants import WALK_MPS
from app.routing.types import GraphEdge, GraphNode, MallGraph

_NS = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


def grid_graph(width: int, height: int, *, cell_m: float = 10.0) -> MallGraph:
    """4-connected directed grid: 2*width*height*(2-ish) hallway edges."""
    floor_id = uuid.uuid5(_NS, "floor")
    nodes: dict[uuid.UUID, GraphNode] = {}
    outgoing: dict[uuid.UUID, list[GraphEdge]] = {}
    coords: dict[tuple[int, int], uuid.UUID] = {}
    for y in range(height):
        for x in range(width):
            nid = uuid.uuid5(_NS, f"{x},{y}")
            coords[(x, y)] = nid
            nodes[nid] = GraphNode(
                id=nid,
                floor_id=floor_id,
                floor_level=0,
                x=x * cell_m,
                y=y * cell_m,
                node_type=NodeType.HALLWAY_JUNCTION,
                location_id=None,
                key=f"{x},{y}",
            )
            outgoing[nid] = []

    def add(a: uuid.UUID, b: uuid.UUID) -> None:
        dist = cell_m
        edge = GraphEdge(
            id=uuid.uuid5(_NS, f"{a}->{b}"),
            from_id=a,
            to_id=b,
            distance_m=dist,
            avg_seconds=dist / WALK_MPS,
            accessible=True,
            edge_type=EdgeType.HALLWAY,
        )
        outgoing[a].append(edge)

    for y in range(height):
        for x in range(width):
            here = coords[(x, y)]
            if x + 1 < width:
                add(here, coords[(x + 1, y)])
                add(coords[(x + 1, y)], here)
            if y + 1 < height:
                add(here, coords[(x, y + 1)])
                add(coords[(x, y + 1)], here)
    by_key = {node.key: node.id for node in nodes.values() if node.key}
    return MallGraph(nodes=nodes, outgoing=outgoing, by_key=by_key)
