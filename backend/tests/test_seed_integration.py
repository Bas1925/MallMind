"""Integration: migrate a real Postgres, seed NOVA Mall, query relationships."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Category, Floor, Location, Mall, MapEdge, MapNode
from app.models.enums import EdgeType, NodeType
from app.seed.nova_mall import build_nova_mall


@pytest.mark.asyncio
async def test_seed_counts_and_relationships(seeded_session: AsyncSession) -> None:
    doc = build_nova_mall()
    nova = await seeded_session.scalar(select(Mall).where(Mall.slug == "nova-mall"))
    assert nova is not None

    floor_count = await seeded_session.scalar(
        select(func.count()).select_from(Floor).where(Floor.mall_id == nova.id)
    )
    location_count = await seeded_session.scalar(
        select(func.count()).select_from(Location).where(Location.mall_id == nova.id)
    )
    nova_nodes = await seeded_session.scalar(
        select(func.count())
        .select_from(MapNode)
        .join(Floor, MapNode.floor_id == Floor.id)
        .where(Floor.mall_id == nova.id)
    )
    nova_edges = await seeded_session.scalar(
        select(func.count())
        .select_from(MapEdge)
        .join(MapNode, MapEdge.from_node_id == MapNode.id)
        .join(Floor, MapNode.floor_id == Floor.id)
        .where(Floor.mall_id == nova.id)
    )
    category_count = await seeded_session.scalar(select(func.count()).select_from(Category))

    assert floor_count == 3
    assert location_count == len(doc.locations)
    assert nova_nodes == len(doc.nodes)
    assert nova_edges == len(doc.edges)
    assert category_count >= len(doc.categories)

    nike = await seeded_session.scalar(
        select(Location)
        .options(
            selectinload(Location.anchor_node),
            selectinload(Location.floor),
            selectinload(Location.category),
        )
        .where(Location.slug == "nike")
    )
    assert nike is not None
    assert nike.anchor_node is not None
    assert nike.anchor_node.node_type == NodeType.STORE_ANCHOR
    assert nike.floor.name == "Ground Floor"
    assert nike.category.slug == "fashion"

    elevator_edges = (
        await seeded_session.scalars(select(MapEdge).where(MapEdge.edge_type == EdgeType.ELEVATOR))
    ).all()
    assert len(elevator_edges) == 4  # two adjacent pairs, both directions
    assert all(edge.accessible for edge in elevator_edges)

    stairs_edges = (
        await seeded_session.scalars(select(MapEdge).where(MapEdge.edge_type == EdgeType.STAIRS))
    ).all()
    assert len(stairs_edges) == 4
    assert all(not edge.accessible for edge in stairs_edges)

    # Escalators are one-way.
    up = (
        await seeded_session.scalars(
            select(MapEdge).where(MapEdge.edge_type == EdgeType.ESCALATOR_UP)
        )
    ).all()
    down = (
        await seeded_session.scalars(
            select(MapEdge).where(MapEdge.edge_type == EdgeType.ESCALATOR_DOWN)
        )
    ).all()
    assert len(up) == 2
    assert len(down) == 2

    # A raw SQL join: every location on nova-mall has exactly one anchor node.
    result = await seeded_session.execute(
        text(
            """
            SELECT l.slug, COUNT(n.id) AS anchors
            FROM locations l
            LEFT JOIN map_nodes n ON n.location_id = l.id
            JOIN malls m ON m.id = l.mall_id
            WHERE m.slug = 'nova-mall'
            GROUP BY l.slug
            HAVING COUNT(n.id) <> 1
            """
        )
    )
    assert result.fetchall() == []
