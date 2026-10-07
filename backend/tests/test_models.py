"""Postgres constraint tests.

These hit a real PostgreSQL (not SQLite). They skip when the database
is unreachable so unit tests still run on a laptop without Docker.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Category, Floor, Location, Mall, MapEdge, MapNode
from app.models.enums import EdgeType, NodeType
from tests.db_support import alembic_upgrade_head, database_url, postgres_reachable


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    url = database_url()
    if not postgres_reachable(url):
        pytest.skip("PostgreSQL is not reachable")
    alembic_upgrade_head()
    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()
    await engine.dispose()


async def _mall_floor_category(session: AsyncSession) -> tuple[Mall, Floor, Category]:
    mall = Mall(
        id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:10]}", name="Test Mall", timezone="UTC"
    )
    session.add(mall)
    await session.flush()
    floor = Floor(id=uuid.uuid4(), mall_id=mall.id, level=0, name="Ground", display_order=0)
    session.add(floor)
    category = Category(
        slug=f"cat-{uuid.uuid4().hex[:8]}",
        name_en="Fashion",
        name_he="אופנה",
        name_ar="أزياء",
    )
    session.add(category)
    await session.flush()
    return mall, floor, category


@pytest.mark.asyncio
async def test_duplicate_location_slug_is_rejected(db_session: AsyncSession) -> None:
    mall, floor, category = await _mall_floor_category(db_session)
    shared = {"mall_id": mall.id, "floor_id": floor.id, "category_id": category.id, "slug": "nike"}
    db_session.add(Location(id=uuid.uuid4(), name="Nike A", **shared))
    await db_session.flush()
    db_session.add(Location(id=uuid.uuid4(), name="Nike B", **shared))
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_invalid_floor_fk_is_rejected(db_session: AsyncSession) -> None:
    mall, _floor, category = await _mall_floor_category(db_session)
    db_session.add(
        Location(
            id=uuid.uuid4(),
            mall_id=mall.id,
            floor_id=uuid.uuid4(),
            category_id=category.id,
            slug="ghost",
            name="Ghost",
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_negative_edge_distance_is_rejected(db_session: AsyncSession) -> None:
    _mall, floor, _category = await _mall_floor_category(db_session)
    a = MapNode(
        id=uuid.uuid4(),
        floor_id=floor.id,
        x=0.0,
        y=0.0,
        node_type=NodeType.HALLWAY_JUNCTION,
    )
    b = MapNode(
        id=uuid.uuid4(),
        floor_id=floor.id,
        x=10.0,
        y=0.0,
        node_type=NodeType.HALLWAY_JUNCTION,
    )
    db_session.add_all([a, b])
    await db_session.flush()
    db_session.add(
        MapEdge(
            id=uuid.uuid4(),
            from_node_id=a.id,
            to_node_id=b.id,
            distance_m=-1.0,
            edge_type=EdgeType.HALLWAY,
            accessible=True,
            avg_seconds=5.0,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_self_loop_edge_is_rejected(db_session: AsyncSession) -> None:
    _mall, floor, _category = await _mall_floor_category(db_session)
    node = MapNode(
        id=uuid.uuid4(),
        floor_id=floor.id,
        x=0.0,
        y=0.0,
        node_type=NodeType.HALLWAY_JUNCTION,
    )
    db_session.add(node)
    await db_session.flush()
    db_session.add(
        MapEdge(
            id=uuid.uuid4(),
            from_node_id=node.id,
            to_node_id=node.id,
            distance_m=5.0,
            edge_type=EdgeType.HALLWAY,
            accessible=True,
            avg_seconds=4.0,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_duplicate_directed_edge_is_rejected(db_session: AsyncSession) -> None:
    _mall, floor, _category = await _mall_floor_category(db_session)
    a = MapNode(
        id=uuid.uuid4(),
        floor_id=floor.id,
        x=0.0,
        y=0.0,
        node_type=NodeType.HALLWAY_JUNCTION,
    )
    b = MapNode(
        id=uuid.uuid4(),
        floor_id=floor.id,
        x=10.0,
        y=0.0,
        node_type=NodeType.HALLWAY_JUNCTION,
    )
    db_session.add_all([a, b])
    await db_session.flush()
    kwargs = {
        "from_node_id": a.id,
        "to_node_id": b.id,
        "distance_m": 10.0,
        "edge_type": EdgeType.HALLWAY,
        "accessible": True,
        "avg_seconds": 8.0,
    }
    db_session.add(MapEdge(id=uuid.uuid4(), **kwargs))
    await db_session.flush()
    db_session.add(MapEdge(id=uuid.uuid4(), **kwargs))
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_duplicate_mall_slug_is_rejected(db_session: AsyncSession) -> None:
    slug = f"dup-{uuid.uuid4().hex[:8]}"
    db_session.add(Mall(id=uuid.uuid4(), slug=slug, name="A", timezone="UTC"))
    await db_session.flush()
    db_session.add(Mall(id=uuid.uuid4(), slug=slug, name="B", timezone="UTC"))
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_node_type_persists_enum_value_not_name(db_session: AsyncSession) -> None:
    """Regression: StrEnum member names must not be sent to Postgres ENUMs."""
    from sqlalchemy import text

    _mall, floor, _category = await _mall_floor_category(db_session)
    node = MapNode(
        id=uuid.uuid4(),
        floor_id=floor.id,
        x=1.0,
        y=2.0,
        node_type=NodeType.HALLWAY_JUNCTION,
    )
    db_session.add(node)
    await db_session.flush()
    stored = (
        await db_session.execute(
            text("SELECT node_type::text FROM map_nodes WHERE id = :id"),
            {"id": node.id},
        )
    ).scalar_one()
    assert stored == "hallway_junction"
