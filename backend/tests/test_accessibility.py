"""Route profiles filter edges; algorithms stay unaware of stairs vs elevators."""

from __future__ import annotations

from app.models.enums import EdgeType
from app.routing.astar import astar
from app.routing.dijkstra import dijkstra
from app.routing.graph import graph_from_seed
from app.routing.policy import filter_for
from app.routing.types import RouteProfile
from app.seed.nova_mall import build_nova_mall
from tests.routing_graphs import nid, path_edge_types, two_floor_vertical


def test_normal_chooses_stairs_when_they_are_shortest() -> None:
    g = two_floor_vertical()
    allow = filter_for(RouteProfile.NORMAL)
    result = dijkstra(g, nid("g-west"), nid("u-west"), allow=allow)
    assert result.ok
    assert EdgeType.STAIRS in path_edge_types(g, result.edge_ids)
    assert EdgeType.ELEVATOR not in path_edge_types(g, result.edge_ids)


def test_wheelchair_uses_elevator_not_stairs() -> None:
    g = two_floor_vertical()
    allow = filter_for(RouteProfile.WHEELCHAIR)
    result = astar(g, nid("g-west"), nid("u-west"), allow=allow)
    assert result.ok
    types = path_edge_types(g, result.edge_ids)
    assert EdgeType.ELEVATOR in types
    assert EdgeType.STAIRS not in types
    baseline = dijkstra(g, nid("g-west"), nid("u-west"), allow=allow)
    assert result.total_distance_m == baseline.total_distance_m


def test_wheelchair_reports_no_path_when_only_stairs_exist() -> None:
    g = two_floor_vertical(stairs_only=True)
    result = astar(g, nid("g-west"), nid("u-west"), allow=filter_for(RouteProfile.WHEELCHAIR))
    assert not result.ok
    assert result.failure_reason == "no_path"
    normal = astar(g, nid("g-west"), nid("u-west"), allow=filter_for(RouteProfile.NORMAL))
    assert normal.ok


def test_avoid_stairs_excludes_stair_edges_on_nova() -> None:
    g = graph_from_seed(build_nova_mall())
    start = g.node_by_key("loc-restroom-g-north").id
    goal = g.node_by_key("loc-restroom-l1").id
    normal = astar(g, start, goal, allow=filter_for(RouteProfile.NORMAL))
    avoid = astar(g, start, goal, allow=filter_for(RouteProfile.AVOID_STAIRS))
    chair = astar(g, start, goal, allow=filter_for(RouteProfile.WHEELCHAIR))
    assert normal.ok and avoid.ok and chair.ok
    assert EdgeType.STAIRS in path_edge_types(g, normal.edge_ids)
    assert EdgeType.STAIRS not in path_edge_types(g, avoid.edge_ids)
    assert EdgeType.STAIRS not in path_edge_types(g, chair.edge_ids)
    assert EdgeType.ELEVATOR in path_edge_types(g, chair.edge_ids)
