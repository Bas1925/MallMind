"""Unit tests for Dijkstra, A*, profiles, and walking instructions.

These tests use in-memory graphs only. They do not need PostgreSQL.
"""

from __future__ import annotations

import math
import uuid

import pytest

from app.models.enums import EdgeType, NodeType
from app.routing.astar import astar
from app.routing.dijkstra import dijkstra
from app.routing.graph import graph_from_seed
from app.routing.heuristic import heuristic
from app.routing.instructions import floors_on_route, instructions_for
from app.routing.policy import filter_for
from app.routing.synthetic import grid_graph
from app.routing.types import CostMode, GraphEdge, GraphNode, MallGraph, RouteProfile
from app.seed.nova_mall import build_nova_mall

_NS = uuid.UUID("bbbbbbbb-cccc-dddd-eeee-ffffffffffff")


def _node(
    key: str,
    *,
    level: int = 0,
    x: float = 0.0,
    y: float = 0.0,
    node_type: NodeType = NodeType.HALLWAY_JUNCTION,
) -> GraphNode:
    nid = uuid.uuid5(_NS, key)
    return GraphNode(
        id=nid,
        floor_id=uuid.uuid5(_NS, f"floor:{level}"),
        floor_level=level,
        x=x,
        y=y,
        node_type=node_type,
        location_id=None,
        key=key,
    )


def _edge(
    a: GraphNode,
    b: GraphNode,
    *,
    distance_m: float,
    avg_seconds: float | None = None,
    accessible: bool = True,
    edge_type: EdgeType = EdgeType.HALLWAY,
) -> GraphEdge:
    seconds = avg_seconds if avg_seconds is not None else distance_m / 1.25
    return GraphEdge(
        id=uuid.uuid5(_NS, f"{a.key}->{b.key}"),
        from_id=a.id,
        to_id=b.id,
        distance_m=distance_m,
        avg_seconds=seconds,
        accessible=accessible,
        edge_type=edge_type,
    )


def _graph(nodes: list[GraphNode], edges: list[GraphEdge]) -> MallGraph:
    outgoing: dict[uuid.UUID, list[GraphEdge]] = {n.id: [] for n in nodes}
    by_key = {n.key: n.id for n in nodes if n.key}
    for edge in edges:
        outgoing[edge.from_id].append(edge)
    return MallGraph(
        nodes={n.id: n for n in nodes},
        outgoing=outgoing,
        by_key=by_key,
    )


@pytest.fixture(scope="module")
def nova() -> MallGraph:
    return graph_from_seed(build_nova_mall())


def test_same_node_is_trivial_success(nova: MallGraph) -> None:
    start = nova.node_by_key("loc-nike").id
    for algo in (dijkstra, astar):
        result = algo(nova, start, start)
        assert result.ok
        assert result.node_ids == (start,)
        assert result.edge_ids == ()
        assert result.total_distance_m == 0.0


def test_unknown_node_fails(nova: MallGraph) -> None:
    start = nova.node_by_key("loc-nike").id
    missing = uuid.uuid4()
    result = dijkstra(nova, start, missing)
    assert not result.ok
    assert result.failure_reason == "unknown_node"


def test_dijkstra_and_astar_agree_on_nova_pairs(nova: MallGraph) -> None:
    pairs = (
        ("loc-nike", "loc-zara"),
        ("loc-nike", "loc-apple"),
        ("loc-main-entrance", "loc-rooftop-cafe"),
        ("loc-parking-entrance", "loc-muji"),
        ("elev-ground", "elev-l2"),
    )
    for src_key, dst_key in pairs:
        start = nova.node_by_key(src_key).id
        goal = nova.node_by_key(dst_key).id
        for mode in (CostMode.DISTANCE, CostMode.TIME):
            d = dijkstra(nova, start, goal, cost_mode=mode)
            a = astar(nova, start, goal, cost_mode=mode)
            assert d.ok and a.ok, (src_key, dst_key, mode, d.failure_reason, a.failure_reason)
            assert d.total_distance_m == pytest.approx(a.total_distance_m, rel=1e-9, abs=1e-9)
            assert d.total_seconds == pytest.approx(a.total_seconds, rel=1e-9, abs=1e-9)


def test_location_to_location_via_anchors(nova: MallGraph) -> None:
    start = nova.node_by_key("loc-nike").id
    goal = nova.node_by_key("loc-apple").id
    result = astar(nova, start, goal)
    assert result.ok
    assert result.node_ids[0] == start
    assert result.node_ids[-1] == goal
    assert result.total_distance_m > 0
    levels = floors_on_route(nova, result.node_ids)
    assert levels[0] == 0
    assert 1 in levels


def test_wheelchair_avoids_stairs_and_escalators(nova: MallGraph) -> None:
    start = nova.node_by_key("loc-nike").id
    goal = nova.node_by_key("loc-apple").id
    result = astar(nova, start, goal, allow=filter_for(RouteProfile.WHEELCHAIR))
    assert result.ok
    banned = {EdgeType.STAIRS, EdgeType.ESCALATOR_UP, EdgeType.ESCALATOR_DOWN}
    used = {e.edge_type for e in nova.edges_on(result)}
    assert used.isdisjoint(banned)
    assert EdgeType.ELEVATOR in used


def test_avoid_stairs_still_may_use_escalator(nova: MallGraph) -> None:
    start = nova.node_by_key("loc-nike").id
    goal = nova.node_by_key("loc-apple").id
    result = astar(nova, start, goal, allow=filter_for(RouteProfile.AVOID_STAIRS))
    assert result.ok
    used = {e.edge_type for e in nova.edges_on(result)}
    assert EdgeType.STAIRS not in used


def test_wheelchair_fails_when_only_stairs_exist() -> None:
    ground = _node("g", level=0, x=0, y=0, node_type=NodeType.STAIRS_LANDING)
    upper = _node("u", level=1, x=0, y=0, node_type=NodeType.STAIRS_LANDING)
    stairs = _edge(
        ground,
        upper,
        distance_m=12.0,
        avg_seconds=40.0,
        accessible=False,
        edge_type=EdgeType.STAIRS,
    )
    graph = _graph([ground, upper], [stairs])
    normal = dijkstra(graph, ground.id, upper.id, allow=filter_for(RouteProfile.NORMAL))
    chair = dijkstra(graph, ground.id, upper.id, allow=filter_for(RouteProfile.WHEELCHAIR))
    assert normal.ok
    assert not chair.ok
    assert chair.failure_reason == "no_path"


def test_escalator_is_one_way() -> None:
    lower = _node("esc-g", level=0, x=90, y=48, node_type=NodeType.ESCALATOR_UP_LANDING)
    upper = _node("esc-l1", level=1, x=90, y=48, node_type=NodeType.ESCALATOR_UP_LANDING)
    up = _edge(
        lower,
        upper,
        distance_m=8.0,
        avg_seconds=20.0,
        accessible=False,
        edge_type=EdgeType.ESCALATOR_UP,
    )
    graph = _graph([lower, upper], [up])
    ascending = astar(graph, lower.id, upper.id)
    descending = astar(graph, upper.id, lower.id)
    assert ascending.ok
    assert not descending.ok
    assert descending.failure_reason == "no_path"


def test_heuristic_is_planar_euclidean_even_across_floors() -> None:
    a = _node("a", level=0, x=0, y=0)
    b = _node("b", level=2, x=30, y=40)
    metres = heuristic(a, b, CostMode.DISTANCE)
    seconds = heuristic(a, b, CostMode.TIME)
    assert metres == pytest.approx(50.0)
    assert seconds == pytest.approx(50.0 / 1.25)
    same_floor = _node("c", level=0, x=30, y=40)
    assert heuristic(a, same_floor, CostMode.DISTANCE) == pytest.approx(metres)


def test_instructions_walk_then_elevator(nova: MallGraph) -> None:
    start = nova.node_by_key("loc-nike").id
    goal = nova.node_by_key("loc-apple").id
    result = astar(nova, start, goal, allow=filter_for(RouteProfile.WHEELCHAIR))
    steps = instructions_for(nova, result, destination_name="Apple")
    assert any(s.startswith("Walk ") for s in steps)
    assert any("elevator" in s.lower() for s in steps)
    assert steps[-1] == "Arrive at Apple"
    assert 0 in floors_on_route(nova, result.node_ids)


def test_astar_expands_fewer_nodes_when_heuristic_prunes() -> None:
    """Cheap blob north of the start vs a long east corridor to the goal.

    Dijkstra floods the blob (those nodes are close in g). A* has a high
    Euclidean h on the blob and follows the corridor instead.
    """
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    corridor = 25
    for x in range(corridor):
        key = f"c{x}"
        nodes.append(_node(key, x=float(x), y=0.0))
        if x:
            edges.append(_edge(nodes[x - 1], nodes[x], distance_m=1.0))
            edges.append(_edge(nodes[x], nodes[x - 1], distance_m=1.0))
    start = nodes[0]
    for i in range(40):
        blob = _node(f"b{i}", x=0.0, y=20.0 + i)
        nodes.append(blob)
        edges.append(_edge(start, blob, distance_m=1.0))
        edges.append(_edge(blob, start, distance_m=1.0))
    graph = _graph(nodes, edges)
    goal = graph.node_by_key(f"c{corridor - 1}").id
    a = astar(graph, start.id, goal)
    d = dijkstra(graph, start.id, goal)
    assert a.ok and d.ok
    assert a.total_distance_m == pytest.approx(d.total_distance_m)
    assert a.nodes_expanded < d.nodes_expanded


def test_grid_shortest_path_is_manhattan_not_euclidean() -> None:
    graph = grid_graph(40, 40, cell_m=10.0)
    start = graph.node_by_key("0,0").id
    goal = graph.node_by_key("39,39").id
    d = dijkstra(graph, start, goal)
    a = astar(graph, start, goal)
    assert d.ok and a.ok
    assert d.total_distance_m == pytest.approx(a.total_distance_m)
    assert a.nodes_expanded <= d.nodes_expanded
    expected = math.hypot(39 * 10.0, 39 * 10.0)
    # 4-connected grid shortest path is Manhattan, not Euclidean.
    assert d.total_distance_m == pytest.approx(39 * 10.0 + 39 * 10.0)
    assert expected < d.total_distance_m
