"""POST /api/v1/navigation/optimize against seeded NOVA Mall."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Floor, Location, Mall, MapEdge, MapNode
from app.models.enums import EdgeType, NodeType


async def _id(session: AsyncSession, slug: str) -> uuid.UUID:
    loc_id = await session.scalar(select(Location.id).where(Location.slug == slug))
    assert loc_id is not None
    return loc_id


async def _optimize(
    client: AsyncClient,
    session: AsyncSession,
    start: str,
    stops: list[str],
    profile: str = "normal",
) -> dict:
    payload = {
        "start_location_id": str(await _id(session, start)),
        "location_ids": [str(await _id(session, slug)) for slug in stops],
        "profile": profile,
        "cost_mode": "distance",
    }
    response = await client.post("/api/v1/navigation/optimize", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body, dict)
    return body


@pytest.mark.asyncio
async def test_optimize_beats_or_matches_the_submitted_order(
    api_client: AsyncClient, seeded_session: AsyncSession
) -> None:
    body = await _optimize(
        api_client,
        seeded_session,
        "main-entrance",
        ["nike", "zara", "apple", "atm-g", "super-pharm"],
    )
    assert body["algorithm"] in {"held_karp", "nearest_neighbor_2opt", "user_order"}
    assert body["optimized_distance_m"] <= body["original_distance_m"] + 0.05
    assert [stop["position"] for stop in body["optimized_order"]] == [1, 2, 3, 4, 5, 6]
    slugs = {stop["slug"] for stop in body["optimized_order"]}
    assert slugs == {"main-entrance", "nike", "zara", "apple", "atm-g", "super-pharm"}
    assert body["optimized_order"][0]["slug"] == "main-entrance"
    assert body["astar_calls"] == 6 * 5
    assert body["exact_distance_m"] is not None
    assert body["nearest_neighbor_distance_m"] + 0.05 >= body["exact_distance_m"]
    assert body["nearest_neighbor_2opt_distance_m"] + 0.05 >= body["exact_distance_m"]
    if body["improved"]:
        assert body["distance_saved_m"] > 0
        assert body["message"] is None
    else:
        assert body["distance_saved_m"] == 0
        assert body["message"] == "No shorter route was found."
    assert body["node_ids"]
    assert "embedding" not in body


@pytest.mark.asyncio
async def test_optimize_rejects_bad_requests(
    api_client: AsyncClient, seeded_session: AsyncSession
) -> None:
    start = str(await _id(seeded_session, "main-entrance"))
    nike = str(await _id(seeded_session, "nike"))

    empty = await api_client.post(
        "/api/v1/navigation/optimize",
        json={"start_location_id": start, "location_ids": [], "profile": "normal"},
    )
    assert empty.status_code == 400
    assert empty.json()["code"] == "empty_stops"

    duplicate = await api_client.post(
        "/api/v1/navigation/optimize",
        json={"start_location_id": start, "location_ids": [nike, nike], "profile": "normal"},
    )
    assert duplicate.status_code == 400
    assert duplicate.json()["code"] == "duplicate_stop"

    unknown = await api_client.post(
        "/api/v1/navigation/optimize",
        json={
            "start_location_id": start,
            "location_ids": [str(uuid.uuid4())],
            "profile": "normal",
        },
    )
    assert unknown.status_code == 404
    assert unknown.json()["code"] == "unknown_location"

    too_many = await api_client.post(
        "/api/v1/navigation/optimize",
        json={"start_location_id": start, "location_ids": [str(uuid.uuid4()) for _ in range(21)]},
    )
    assert too_many.status_code == 400
    assert too_many.json()["code"] == "too_many_stops"


@pytest.mark.asyncio
async def test_wheelchair_matrix_can_differ(
    api_client: AsyncClient, seeded_session: AsyncSession
) -> None:
    normal = await _optimize(
        api_client,
        seeded_session,
        "restroom-g-north",
        ["restroom-l1", "nike"],
        profile="normal",
    )
    chair = await _optimize(
        api_client,
        seeded_session,
        "restroom-g-north",
        ["restroom-l1", "nike"],
        profile="wheelchair",
    )
    assert normal["profile"] == "normal"
    assert chair["profile"] == "wheelchair"
    assert (
        normal["matrix_m"] != chair["matrix_m"]
        or normal["optimized_distance_m"] != chair["optimized_distance_m"]
    )


@pytest.mark.asyncio
async def test_unreachable_stop_fails_the_plan(
    api_client: AsyncClient, seeded_session: AsyncSession
) -> None:
    mall = await seeded_session.scalar(select(Mall).where(Mall.slug == "nova-mall"))
    floor = await seeded_session.scalar(select(Floor).where(Floor.mall_id == mall.id))
    category = await seeded_session.scalar(select(Category))
    assert mall is not None and floor is not None and category is not None
    loc_a = Location(
        id=uuid.uuid4(),
        mall_id=mall.id,
        floor_id=floor.id,
        category_id=category.id,
        slug="island-a",
        name="Island A",
    )
    loc_b = Location(
        id=uuid.uuid4(),
        mall_id=mall.id,
        floor_id=floor.id,
        category_id=category.id,
        slug="island-b",
        name="Island B",
    )
    seeded_session.add_all([loc_a, loc_b])
    await seeded_session.flush()
    node_a = MapNode(
        id=uuid.uuid4(),
        floor_id=floor.id,
        location_id=loc_a.id,
        x=500.0,
        y=500.0,
        node_type=NodeType.STORE_ANCHOR,
    )
    node_b = MapNode(
        id=uuid.uuid4(),
        floor_id=floor.id,
        location_id=loc_b.id,
        x=500.0,
        y=508.0,
        node_type=NodeType.STORE_ANCHOR,
    )
    seeded_session.add_all([node_a, node_b])
    await seeded_session.flush()
    seeded_session.add(
        MapEdge(
            id=uuid.uuid4(),
            from_node_id=node_a.id,
            to_node_id=node_b.id,
            distance_m=8.0,
            avg_seconds=30.0,
            accessible=False,
            edge_type=EdgeType.STAIRS,
        )
    )
    await seeded_session.flush()

    blocked = await api_client.post(
        "/api/v1/navigation/optimize",
        json={
            "start_location_id": str(loc_a.id),
            "location_ids": [str(loc_b.id)],
            "profile": "wheelchair",
        },
    )
    assert blocked.status_code == 422, blocked.text
    body = blocked.json()
    assert body["code"] == "unreachable_stop"
    assert body["message"] == "No wheelchair-accessible route exists to Island B."
    assert body["location_ids"] == [str(loc_b.id)]

    ok = await api_client.post(
        "/api/v1/navigation/optimize",
        json={
            "start_location_id": str(loc_a.id),
            "location_ids": [str(loc_b.id)],
            "profile": "normal",
        },
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["optimized_distance_m"] == 8.0
