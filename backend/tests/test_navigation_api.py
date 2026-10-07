"""POST /api/v1/navigation/route against a real seeded PostgreSQL."""

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


@pytest.mark.asyncio
async def test_valid_route(api_client: AsyncClient, seeded_session: AsyncSession) -> None:
    src = await _id(seeded_session, "nike")
    dst = await _id(seeded_session, "zara")
    response = await api_client.post(
        "/api/v1/navigation/route",
        json={
            "from_location_id": str(src),
            "to_location_id": str(dst),
            "profile": "normal",
            "cost_mode": "distance",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["algorithm"] == "astar"
    assert body["from_location"] == "Nike"
    assert body["to_location"] == "Zara"
    assert body["distance_m"] > 0
    assert body["estimated_seconds"] > 0
    assert body["instructions"][-1] == "Arrive at Zara"
    assert body["route"]
    assert body["floors"] == [0]


@pytest.mark.asyncio
async def test_unknown_ids(api_client: AsyncClient, seeded_session: AsyncSession) -> None:
    src = await _id(seeded_session, "nike")
    response = await api_client.post(
        "/api/v1/navigation/route",
        json={"from_location_id": str(src), "to_location_id": str(uuid.uuid4())},
    )
    assert response.status_code == 404
    assert response.json()["code"] == "unknown_location"


@pytest.mark.asyncio
async def test_same_location(api_client: AsyncClient, seeded_session: AsyncSession) -> None:
    src = await _id(seeded_session, "nike")
    response = await api_client.post(
        "/api/v1/navigation/route",
        json={"from_location_id": str(src), "to_location_id": str(src)},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "same_location"


@pytest.mark.asyncio
async def test_invalid_profile(api_client: AsyncClient, seeded_session: AsyncSession) -> None:
    src = await _id(seeded_session, "nike")
    dst = await _id(seeded_session, "zara")
    response = await api_client.post(
        "/api/v1/navigation/route",
        json={
            "from_location_id": str(src),
            "to_location_id": str(dst),
            "profile": "hoverboard",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_inaccessible_route(api_client: AsyncClient, seeded_session: AsyncSession) -> None:
    mall = await seeded_session.scalar(select(Mall).where(Mall.slug == "nova-mall"))
    floor = await seeded_session.scalar(select(Floor).where(Floor.mall_id == mall.id))
    category = await seeded_session.scalar(select(Category))
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
        "/api/v1/navigation/route",
        json={
            "from_location_id": str(loc_a.id),
            "to_location_id": str(loc_b.id),
            "profile": "wheelchair",
        },
    )
    assert blocked.status_code == 422, blocked.text
    assert blocked.json()["code"] == "no_accessible_path"

    ok = await api_client.post(
        "/api/v1/navigation/route",
        json={
            "from_location_id": str(loc_a.id),
            "to_location_id": str(loc_b.id),
            "profile": "normal",
        },
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["distance_m"] == 8.0
