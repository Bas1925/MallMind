"""NavigationService: Location IDs in, graph algorithms stay Location-free."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Floor, Location, Mall
from app.routing.dijkstra import dijkstra
from app.routing.graph import graph_from_seed
from app.seed.nova_mall import build_nova_mall
from app.services.navigation import NavigationError, NavigationService


async def _loc(session: AsyncSession, slug: str) -> Location:
    loc = await session.scalar(select(Location).where(Location.slug == slug))
    assert loc is not None
    return loc


@pytest.mark.asyncio
async def test_nike_to_zara_matches_seed_graph_cost(seeded_session: AsyncSession) -> None:
    nike = await _loc(seeded_session, "nike")
    zara = await _loc(seeded_session, "zara")
    nav = await NavigationService(seeded_session).route(nike.id, zara.id, algorithm="dijkstra")
    assert nav.result.ok
    assert nav.from_location.name == "Nike"
    assert nav.to_location.name == "Zara"
    seed = graph_from_seed(build_nova_mall())
    expected = dijkstra(seed, seed.node_by_key("loc-nike").id, seed.node_by_key("loc-zara").id)
    assert nav.result.total_distance_m == expected.total_distance_m
    assert nav.instructions[-1] == "Arrive at Zara"


@pytest.mark.asyncio
async def test_same_location_is_rejected(seeded_session: AsyncSession) -> None:
    nike = await _loc(seeded_session, "nike")
    with pytest.raises(NavigationError) as exc:
        await NavigationService(seeded_session).route(nike.id, nike.id)
    assert exc.value.code == "same_location"
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_unknown_location_is_rejected(seeded_session: AsyncSession) -> None:
    nike = await _loc(seeded_session, "nike")
    with pytest.raises(NavigationError) as exc:
        await NavigationService(seeded_session).route(nike.id, uuid.uuid4())
    assert exc.value.code == "unknown_location"
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_missing_anchor_is_rejected(seeded_session: AsyncSession) -> None:
    mall = await seeded_session.scalar(select(Mall).where(Mall.slug == "nova-mall"))
    floor = await seeded_session.scalar(select(Floor).where(Floor.mall_id == mall.id))
    category = await seeded_session.scalar(select(Category))
    orphan = Location(
        id=uuid.uuid4(),
        mall_id=mall.id,
        floor_id=floor.id,
        category_id=category.id,
        slug="orphan-kiosk",
        name="Orphan Kiosk",
    )
    seeded_session.add(orphan)
    await seeded_session.flush()
    nike = await _loc(seeded_session, "nike")
    with pytest.raises(NavigationError) as exc:
        await NavigationService(seeded_session).route(nike.id, orphan.id)
    assert exc.value.code == "missing_anchor"
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_cross_floor_location_route(seeded_session: AsyncSession) -> None:
    nike = await _loc(seeded_session, "nike")
    apple = await _loc(seeded_session, "apple")
    nav = await NavigationService(seeded_session).route(nike.id, apple.id)
    assert nav.result.ok
    assert nav.result.algorithm == "astar"
    assert 0 in nav.floors and 1 in nav.floors
    seed = graph_from_seed(build_nova_mall())
    expected = dijkstra(seed, seed.node_by_key("loc-nike").id, seed.node_by_key("loc-apple").id)
    assert nav.result.total_distance_m == expected.total_distance_m
