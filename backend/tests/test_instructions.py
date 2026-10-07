"""Deterministic walking instructions. No LLM."""

from __future__ import annotations

from app.routing.dijkstra import dijkstra
from app.routing.graph import graph_from_seed
from app.routing.instructions import instructions_for
from app.seed.nova_mall import build_nova_mall
from tests.routing_graphs import nid, two_floor_vertical


def test_already_at_destination() -> None:
    g = two_floor_vertical()
    result = dijkstra(g, nid("g-west"), nid("g-west"))
    steps = instructions_for(g, result, destination_name="Nike")
    assert steps == ["Already at Nike"]


def test_walk_then_stairs_then_arrive() -> None:
    g = two_floor_vertical()
    result = dijkstra(g, nid("g-west"), nid("u-west"))
    steps = instructions_for(g, result, destination_name="Apple")
    assert steps[0].startswith("Walk ")
    assert any(s.startswith("Take the stairs to floor ") for s in steps)
    assert steps[-1] == "Arrive at Apple"


def test_nova_instructions_are_deterministic() -> None:
    g = graph_from_seed(build_nova_mall())
    result = dijkstra(g, g.node_by_key("loc-nike").id, g.node_by_key("loc-apple").id)
    a = instructions_for(g, result, destination_name="Apple")
    b = instructions_for(g, result, destination_name="Apple")
    assert a == b
    assert a[-1] == "Arrive at Apple"
    assert any(
        "elevator" in s.lower() or "stairs" in s.lower() or "escalator" in s.lower() for s in a
    )
