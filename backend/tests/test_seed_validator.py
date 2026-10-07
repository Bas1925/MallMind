"""Unit tests for seed validation. No database required."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.enums import EdgeType, NodeType
from app.schemas.seed import SeedEdge, SeedNode
from app.seed.nova_mall import build_nova_mall
from app.seed.validator import assert_valid, validate_seed


def _fatal_kinds(doc) -> set[str]:
    return {i.kind for i in validate_seed(doc) if i.fatal}


def test_nova_mall_seed_is_valid() -> None:
    doc = build_nova_mall()
    assert_valid(doc)
    assert len(doc.floors) == 3
    assert 25 <= len(doc.locations) <= 32
    assert len(doc.nodes) >= 80
    assert len(doc.edges) >= 150


def test_missing_node_reference() -> None:
    doc = build_nova_mall()
    doc.edges.append(
        SeedEdge(
            from_node_key="does-not-exist",
            to_node_key=doc.nodes[0].key,
            distance_m=5.0,
            edge_type=EdgeType.HALLWAY,
            accessible=True,
            avg_seconds=4.0,
        )
    )
    assert "missing_ref" in _fatal_kinds(doc)


def test_duplicate_slug_rejected() -> None:
    doc = build_nova_mall()
    original = doc.locations[0]
    doc.locations.append(
        original.model_copy(update={"name": "Duplicate", "anchor_node_key": doc.nodes[1].key})
    )
    assert "duplicate" in _fatal_kinds(doc)


def test_negative_distance_rejected_by_schema() -> None:
    with pytest.raises(ValidationError):
        SeedEdge(
            from_node_key="a",
            to_node_key="b",
            distance_m=-1.0,
            edge_type=EdgeType.HALLWAY,
            accessible=True,
            avg_seconds=4.0,
        )


def test_zero_hallway_distance_rejected_by_validator() -> None:
    doc = build_nova_mall()
    idx, edge = next((i, e) for i, e in enumerate(doc.edges) if e.edge_type == EdgeType.HALLWAY)
    doc.edges[idx] = edge.model_copy(update={"distance_m": 0.0})
    assert "distance" in _fatal_kinds(doc)


def test_self_loop_rejected() -> None:
    doc = build_nova_mall()
    key = doc.nodes[0].key
    doc.edges.append(
        SeedEdge(
            from_node_key=key,
            to_node_key=key,
            distance_m=5.0,
            edge_type=EdgeType.HALLWAY,
            accessible=True,
            avg_seconds=4.0,
        )
    )
    assert "self_loop" in _fatal_kinds(doc)


def test_illegal_vertical_hallway_across_floors() -> None:
    doc = build_nova_mall()
    ground = next(
        n for n in doc.nodes if n.floor_key == "ground" and n.node_type == NodeType.HALLWAY_JUNCTION
    )
    upper = next(
        n for n in doc.nodes if n.floor_key == "l1" and n.node_type == NodeType.HALLWAY_JUNCTION
    )
    doc.edges.append(
        SeedEdge(
            from_node_key=ground.key,
            to_node_key=upper.key,
            distance_m=8.0,
            edge_type=EdgeType.HALLWAY,
            accessible=True,
            avg_seconds=6.0,
        )
    )
    assert "illegal_vertical" in _fatal_kinds(doc)


def test_stairs_must_connect_adjacent_floors() -> None:
    doc = build_nova_mall()
    ground_stairs = next(n for n in doc.nodes if n.key == "stairs-ground")
    l2_stairs = next(n for n in doc.nodes if n.key == "stairs-l2")
    doc.edges.append(
        SeedEdge(
            from_node_key=ground_stairs.key,
            to_node_key=l2_stairs.key,
            distance_m=24.0,
            edge_type=EdgeType.STAIRS,
            accessible=False,
            avg_seconds=80.0,
        )
    )
    assert "illegal_vertical" in _fatal_kinds(doc)


def test_elevator_on_hallway_nodes_is_illegal() -> None:
    doc = build_nova_mall()
    ground = next(
        n for n in doc.nodes if n.floor_key == "ground" and n.node_type == NodeType.HALLWAY_JUNCTION
    )
    upper = next(
        n for n in doc.nodes if n.floor_key == "l1" and n.node_type == NodeType.HALLWAY_JUNCTION
    )
    doc.edges.append(
        SeedEdge(
            from_node_key=ground.key,
            to_node_key=upper.key,
            distance_m=0.0,
            edge_type=EdgeType.ELEVATOR,
            accessible=True,
            avg_seconds=25.0,
        )
    )
    assert "illegal_vertical" in _fatal_kinds(doc)


def test_unknown_floor_on_node() -> None:
    doc = build_nova_mall()
    doc.nodes.append(
        SeedNode(
            key="orphan-floor",
            floor_key="basement",
            node_type=NodeType.HALLWAY_JUNCTION,
            x=0.0,
            y=0.0,
        )
    )
    assert "missing_ref" in _fatal_kinds(doc)


def test_unknown_location_anchor() -> None:
    doc = build_nova_mall()
    loc = doc.locations[0].model_copy(
        update={"slug": "ghost-store", "anchor_node_key": "missing-node"}
    )
    doc.locations.append(loc)
    kinds = _fatal_kinds(doc)
    assert "missing_ref" in kinds
