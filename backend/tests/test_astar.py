"""A*: optimal cost matches Dijkstra; heuristic stays admissible."""

from __future__ import annotations

import random
import uuid

from app.routing.astar import astar
from app.routing.dijkstra import dijkstra
from app.routing.graph import graph_from_seed
from app.routing.heuristic import heuristic
from app.routing.policy import edge_cost
from app.routing.synthetic import grid_graph
from app.routing.types import CostMode
from app.seed.nova_mall import build_nova_mall
from tests.routing_graphs import disconnected, edge, mall_graph, nid, node, weighted_triangle


def _assert_equal_cost(a, d, mode: CostMode = CostMode.DISTANCE) -> None:
    assert a.ok == d.ok
    if not a.ok:
        assert a.failure_reason == d.failure_reason
        return
    if mode is CostMode.DISTANCE:
        assert a.total_distance_m == d.total_distance_m
    else:
        assert a.total_seconds == d.total_seconds


def test_astar_shortest_matches_dijkstra_on_triangle() -> None:
    g = weighted_triangle()
    start, goal = nid("a"), nid("c")
    a = astar(g, start, goal)
    d = dijkstra(g, start, goal)
    _assert_equal_cost(a, d)
    assert a.node_ids == (nid("a"), nid("b"), nid("c"))


def test_astar_same_node() -> None:
    g = weighted_triangle()
    a = astar(g, nid("a"), nid("a"))
    assert a.ok
    assert a.total_distance_m == 0.0
    assert a.nodes_expanded == 1


def test_astar_no_route() -> None:
    g = disconnected()
    a = astar(g, nid("a"), nid("c"))
    assert not a.ok
    assert a.failure_reason == "no_path"


def test_heuristic_never_exceeds_true_cost_on_grid() -> None:
    g = grid_graph(8, 8)
    goal = g.nodes[uuid.uuid5(uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"), "7,7")]
    for vertex in g.nodes.values():
        true = dijkstra(g, vertex.id, goal.id)
        if not true.ok:
            continue
        h = heuristic(vertex, goal, CostMode.DISTANCE)
        assert h <= true.total_distance_m + 1e-9
        h_t = heuristic(vertex, goal, CostMode.TIME)
        assert h_t <= true.total_seconds + 1e-9


def test_heuristic_is_consistent_on_grid_edges() -> None:
    g = grid_graph(5, 5)
    goal = next(iter(g.nodes.values()))
    for vertex in g.nodes.values():
        hu = heuristic(vertex, goal, CostMode.DISTANCE)
        for link in g.neighbors(vertex.id):
            hv = heuristic(g.nodes[link.to_id], goal, CostMode.DISTANCE)
            assert hu <= edge_cost(link, CostMode.DISTANCE) + hv + 1e-9


def test_astar_matches_dijkstra_on_every_nova_location_pair() -> None:
    g = graph_from_seed(build_nova_mall())
    loc_nodes = [n for n in g.nodes.values() if n.location_id is not None]
    assert len(loc_nodes) == 31
    for mode in (CostMode.DISTANCE, CostMode.TIME):
        for src in loc_nodes:
            for dst in loc_nodes:
                a = astar(g, src.id, dst.id, cost_mode=mode)
                d = dijkstra(g, src.id, dst.id, cost_mode=mode)
                _assert_equal_cost(a, d, mode)


def test_astar_matches_dijkstra_cross_floor_nova() -> None:
    g = graph_from_seed(build_nova_mall())
    pairs = [
        ("loc-nike", "loc-apple"),
        ("loc-main-entrance", "loc-muji"),
        ("loc-parking-entrance", "loc-rooftop-cafe"),
        ("loc-starbucks", "loc-pages-bookstore"),
    ]
    for src_key, dst_key in pairs:
        a = astar(g, g.node_by_key(src_key).id, g.node_by_key(dst_key).id)
        d = dijkstra(g, g.node_by_key(src_key).id, g.node_by_key(dst_key).id)
        _assert_equal_cost(a, d)
        floors = {g.nodes[n].floor_level for n in a.node_ids}
        assert len(floors) >= 2


def test_randomized_grid_pairs_match() -> None:
    rng = random.Random(20261006)
    g = grid_graph(8, 8)
    ids = list(g.nodes)
    for _ in range(20):
        start, goal = rng.choice(ids), rng.choice(ids)
        a = astar(g, start, goal)
        d = dijkstra(g, start, goal)
        _assert_equal_cost(a, d)


def test_astar_expands_fewer_nodes_when_heuristic_prunes() -> None:
    """Cheap blob north of start vs a long east corridor. Dijkstra floods the
    blob; A* should not, because Euclidean h on those nodes is large."""
    nodes = [node(f"c{x}", x=float(x), y=0.0) for x in range(25)]
    edges = []
    for x in range(1, 25):
        edges.append(edge(f"c{x - 1}", f"c{x}", distance_m=1.0))
        edges.append(edge(f"c{x}", f"c{x - 1}", distance_m=1.0))
    for i in range(40):
        nodes.append(node(f"b{i}", x=0.0, y=20.0 + i))
        edges.append(edge("c0", f"b{i}", distance_m=1.0))
        edges.append(edge(f"b{i}", "c0", distance_m=1.0))
    g = mall_graph(nodes, edges)
    a = astar(g, nid("c0"), nid("c24"))
    d = dijkstra(g, nid("c0"), nid("c24"))
    _assert_equal_cost(a, d)
    assert a.nodes_expanded < d.nodes_expanded
