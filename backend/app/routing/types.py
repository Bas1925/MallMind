"""Routing value objects. No I/O, no FastAPI."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum

from app.models.enums import EdgeType, NodeType


class CostMode(StrEnum):
    DISTANCE = "distance"
    TIME = "time"


class RouteProfile(StrEnum):
    NORMAL = "normal"
    WHEELCHAIR = "wheelchair"
    AVOID_STAIRS = "avoid_stairs"


@dataclass(frozen=True, slots=True)
class GraphNode:
    id: uuid.UUID
    floor_id: uuid.UUID
    floor_level: int
    x: float
    y: float
    node_type: NodeType
    location_id: uuid.UUID | None
    key: str | None = None  # seed key; None when loaded from the database


@dataclass(frozen=True, slots=True)
class GraphEdge:
    id: uuid.UUID
    from_id: uuid.UUID
    to_id: uuid.UUID
    distance_m: float
    avg_seconds: float
    accessible: bool
    edge_type: EdgeType


@dataclass(frozen=True, slots=True)
class RouteResult:
    ok: bool
    algorithm: str
    node_ids: tuple[uuid.UUID, ...] = ()
    edge_ids: tuple[uuid.UUID, ...] = ()
    total_distance_m: float = 0.0
    total_seconds: float = 0.0
    nodes_expanded: int = 0
    failure_reason: str | None = None

    @staticmethod
    def fail(algorithm: str, reason: str, nodes_expanded: int = 0) -> RouteResult:
        return RouteResult(
            ok=False, algorithm=algorithm, failure_reason=reason, nodes_expanded=nodes_expanded
        )


@dataclass
class MallGraph:
    """Directed weighted graph as an adjacency list.

    Sparse mall graphs have E ≈ a few times V (grid + spurs + shafts).
    An adjacency list is O(V+E) space and O(degree) neighbour expansion.
    An adjacency matrix would be O(V^2) memory for a graph that is ~3% dense
    even at 100x100.
    """

    nodes: dict[uuid.UUID, GraphNode]
    outgoing: dict[uuid.UUID, list[GraphEdge]] = field(default_factory=dict)
    by_key: dict[str, uuid.UUID] = field(default_factory=dict)
    by_location_id: dict[uuid.UUID, uuid.UUID] = field(default_factory=dict)
    floor_names: dict[int, str] = field(default_factory=dict)  # level -> "Level 1"

    def neighbors(self, node_id: uuid.UUID) -> list[GraphEdge]:
        return self.outgoing.get(node_id, [])

    def get(self, node_id: uuid.UUID) -> GraphNode | None:
        return self.nodes.get(node_id)

    def node_by_key(self, key: str) -> GraphNode:
        return self.nodes[self.by_key[key]]

    def edge_by_id(self, edge_id: uuid.UUID) -> GraphEdge:
        for edges in self.outgoing.values():
            for edge in edges:
                if edge.id == edge_id:
                    return edge
        raise KeyError(edge_id)

    def edges_on(self, result: RouteResult) -> list[GraphEdge]:
        return [self.edge_by_id(eid) for eid in result.edge_ids]
