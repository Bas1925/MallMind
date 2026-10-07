"""Escalator direction comes from directed edges, not algorithm special cases."""

from __future__ import annotations

from app.models.enums import EdgeType
from app.routing.astar import astar
from app.routing.dijkstra import dijkstra
from app.routing.graph import graph_from_seed
from app.seed.nova_mall import build_nova_mall
from tests.routing_graphs import escalator_pair, nid, path_edge_types


def test_up_escalator_cannot_be_ridden_down() -> None:
    g = escalator_pair()
    up = dijkstra(g, nid("up-g"), nid("up-u"))
    down_the_up = dijkstra(g, nid("up-u"), nid("up-g"))
    assert up.ok
    assert path_edge_types(g, up.edge_ids) == [EdgeType.ESCALATOR_UP]
    assert not down_the_up.ok


def test_down_escalator_cannot_be_ridden_up() -> None:
    g = escalator_pair()
    down = astar(g, nid("dn-u"), nid("dn-g"))
    up_the_down = astar(g, nid("dn-g"), nid("dn-u"))
    assert down.ok
    assert path_edge_types(g, down.edge_ids) == [EdgeType.ESCALATOR_DOWN]
    assert not up_the_down.ok


def test_nova_up_escalator_edges_have_no_reverse() -> None:
    g = graph_from_seed(build_nova_mall())
    ups = [
        e for edges in g.outgoing.values() for e in edges if e.edge_type is EdgeType.ESCALATOR_UP
    ]
    downs = [
        e for edges in g.outgoing.values() for e in edges if e.edge_type is EdgeType.ESCALATOR_DOWN
    ]
    assert ups
    assert downs
    up_pairs = {(e.from_id, e.to_id) for e in ups}
    for e in ups:
        assert (e.to_id, e.from_id) not in up_pairs
        assert dijkstra(g, e.from_id, e.to_id).ok
