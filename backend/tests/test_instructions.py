"""Deterministic walking instructions. No LLM."""

from __future__ import annotations

from app.routing.astar import astar
from app.routing.dijkstra import dijkstra
from app.routing.graph import graph_from_seed
from app.routing.instructions import instructions_for
from app.routing.policy import filter_for
from app.routing.types import RouteProfile
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


def test_one_elevator_ride_across_two_floors_is_one_step() -> None:
    g = graph_from_seed(build_nova_mall())
    result = astar(
        g,
        g.node_by_key("loc-main-entrance").id,
        g.node_by_key("loc-muji").id,
        allow=filter_for(RouteProfile.WHEELCHAIR),
    )
    steps = instructions_for(g, result, destination_name="MUJI")
    elevator = [s for s in steps if "elevator" in s]
    assert elevator == ["Take the elevator to Level 2"]
    assert steps[-1] == "Arrive at MUJI"


def test_floor_names_fall_back_to_the_level_number() -> None:
    g = two_floor_vertical()
    result = dijkstra(g, nid("g-west"), nid("u-west"))
    steps = instructions_for(g, result, destination_name="Apple")
    assert "Take the stairs to floor 1" in steps
