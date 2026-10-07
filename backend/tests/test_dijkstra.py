"""Dijkstra: shortest path, directed edges, failure modes, cross-floor."""

from __future__ import annotations

import uuid

from app.models.enums import EdgeType
from app.routing.dijkstra import dijkstra
from app.routing.graph import graph_from_seed
from app.routing.types import CostMode, GraphEdge
from app.seed.nova_mall import build_nova_mall
from tests.routing_graphs import (
    directed_two_node,
    disconnected,
    nid,
    path_edge_types,
    two_floor_vertical,
    weighted_triangle,
)


def test_shortest_route_prefers_cheap_two_edge_path() -> None:
    g = weighted_triangle()
    result = dijkstra(g, nid("a"), nid("c"))
    assert result.ok
    assert result.node_ids == (nid("a"), nid("b"), nid("c"))
    assert result.total_distance_m == 4.0


def test_same_node_is_zero_length() -> None:
    g = weighted_triangle()
    result = dijkstra(g, nid("a"), nid("a"))
    assert result.ok
    assert result.node_ids == (nid("a"),)
    assert result.edge_ids == ()
    assert result.total_distance_m == 0.0
    assert result.total_seconds == 0.0
    assert result.nodes_expanded == 1


def test_no_route_on_disconnected_graph() -> None:
    g = disconnected()
    result = dijkstra(g, nid("a"), nid("c"))
    assert not result.ok
    assert result.failure_reason == "no_path"


def test_unknown_node_fails() -> None:
    g = weighted_triangle()
    result = dijkstra(g, nid("a"), uuid.uuid4())
    assert not result.ok
    assert result.failure_reason == "unknown_node"


def test_directed_edge_is_not_implicitly_reversed() -> None:
    g = directed_two_node()
    forward = dijkstra(g, nid("a"), nid("b"))
    assert forward.ok
    reverse = dijkstra(g, nid("b"), nid("a"))
    assert not reverse.ok
    assert reverse.failure_reason == "no_path"


def test_positive_weights_sum_along_path() -> None:
    g = weighted_triangle()
    result = dijkstra(g, nid("a"), nid("c"))
    assert result.total_distance_m == 4.0
    assert result.total_seconds == 4.0 / 1.25


def test_cross_floor_uses_vertical_edge() -> None:
    g = two_floor_vertical()
    result = dijkstra(g, nid("g-west"), nid("u-west"))
    assert result.ok
    types = path_edge_types(g, result.edge_ids)
    assert EdgeType.STAIRS in types
    assert result.total_distance_m == 10.0  # 1 + 8 + 1


def test_time_mode_optimizes_seconds_not_metres() -> None:
    g = two_floor_vertical()
    by_distance = dijkstra(g, nid("g-west"), nid("u-west"), cost_mode=CostMode.DISTANCE)
    by_time = dijkstra(g, nid("g-west"), nid("u-west"), cost_mode=CostMode.TIME)
    assert by_distance.ok and by_time.ok
    assert by_distance.total_distance_m == by_time.total_distance_m
    assert by_distance.total_seconds == by_time.total_seconds
    slow_stairs = two_floor_vertical()
    # Make the stair flight expensive in time so the elevator wins on TIME only.
    for edges in slow_stairs.outgoing.values():
        for i, e in enumerate(edges):
            if e.edge_type is EdgeType.STAIRS:
                edges[i] = GraphEdge(
                    id=e.id,
                    from_id=e.from_id,
                    to_id=e.to_id,
                    distance_m=e.distance_m,
                    avg_seconds=500.0,
                    accessible=e.accessible,
                    edge_type=e.edge_type,
                )
    dist = dijkstra(slow_stairs, nid("g-west"), nid("u-west"), cost_mode=CostMode.DISTANCE)
    time = dijkstra(slow_stairs, nid("g-west"), nid("u-west"), cost_mode=CostMode.TIME)
    assert EdgeType.STAIRS in path_edge_types(slow_stairs, dist.edge_ids)
    assert EdgeType.ELEVATOR in path_edge_types(slow_stairs, time.edge_ids)


def test_nova_same_floor_nike_to_zara() -> None:
    g = graph_from_seed(build_nova_mall())
    result = dijkstra(g, g.node_by_key("loc-nike").id, g.node_by_key("loc-zara").id)
    assert result.ok
    assert result.total_distance_m > 0
    floors = {g.nodes[n].floor_level for n in result.node_ids}
    assert floors == {0}
