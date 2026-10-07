"""Database writes for the mall seed.

This is the only Phase 1 repository. It exists because the CLI and the
integration tests share the same insert/delete order; extracting it once
avoids two copies of the FK-sensitive sequence.
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Floor, Location, Mall, MapEdge, MapNode
from app.schemas.seed import SeedDocument


class SeedRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_mall_by_slug(self, slug: str) -> Mall | None:
        return await self._session.scalar(select(Mall).where(Mall.slug == slug))

    async def delete_mall_graph(self, mall: Mall) -> None:
        """Delete a mall and everything that hangs off it.

        Categories are global and are left in place. Children are deleted
        explicitly because the FKs are ON DELETE RESTRICT.
        """
        floor_ids = list(
            (await self._session.scalars(select(Floor.id).where(Floor.mall_id == mall.id))).all()
        )
        node_ids = []
        if floor_ids:
            node_ids = list(
                (
                    await self._session.scalars(
                        select(MapNode.id).where(MapNode.floor_id.in_(floor_ids))
                    )
                ).all()
            )
        if node_ids:
            await self._session.execute(
                delete(MapEdge).where(
                    or_(MapEdge.from_node_id.in_(node_ids), MapEdge.to_node_id.in_(node_ids))
                )
            )
            await self._session.execute(delete(MapNode).where(MapNode.id.in_(node_ids)))
        await self._session.execute(delete(Location).where(Location.mall_id == mall.id))
        await self._session.execute(delete(Floor).where(Floor.mall_id == mall.id))
        await self._session.delete(mall)
        await self._session.flush()

    async def insert_document(self, doc: SeedDocument) -> Mall:
        """Insert a validated seed. Caller is responsible for validation."""
        mall = Mall(
            id=uuid.uuid4(),
            slug=doc.mall.slug,
            name=doc.mall.name,
            city=doc.mall.city,
            timezone=doc.mall.timezone,
        )
        self._session.add(mall)
        await self._session.flush()

        floors: dict[str, Floor] = {}
        for item in doc.floors:
            floor = Floor(
                id=uuid.uuid4(),
                mall_id=mall.id,
                level=item.level,
                name=item.name,
                display_order=item.display_order,
            )
            self._session.add(floor)
            floors[item.key] = floor
        await self._session.flush()

        categories: dict[str, Category] = {}
        for item in doc.categories:
            existing = await self._session.scalar(
                select(Category).where(Category.slug == item.slug)
            )
            if existing is not None:
                categories[item.slug] = existing
                continue
            category = Category(
                slug=item.slug,
                name_en=item.name_en,
                name_he=item.name_he,
                name_ar=item.name_ar,
            )
            self._session.add(category)
            await self._session.flush()
            categories[item.slug] = category

        locations: dict[str, Location] = {}
        for item in doc.locations:
            location = Location(
                id=uuid.uuid4(),
                mall_id=mall.id,
                floor_id=floors[item.floor_key].id,
                category_id=categories[item.category_slug].id,
                slug=item.slug,
                name=item.name,
                description=item.description,
                wheelchair_accessible=item.wheelchair_accessible,
                is_active=True,
            )
            self._session.add(location)
            locations[item.slug] = location
        await self._session.flush()

        # Prefer the location's explicit anchor pointer; `node.location_slug`
        # is a convenience field that must agree with it when set.
        anchor_slug_by_node = {loc.anchor_node_key: loc.slug for loc in doc.locations}

        nodes: dict[str, MapNode] = {}
        for item in doc.nodes:
            slug = item.location_slug or anchor_slug_by_node.get(item.key)
            location_id = locations[slug].id if slug is not None else None
            node = MapNode(
                id=uuid.uuid4(),
                floor_id=floors[item.floor_key].id,
                location_id=location_id,
                x=item.x,
                y=item.y,
                node_type=item.node_type,
            )
            self._session.add(node)
            nodes[item.key] = node
        await self._session.flush()

        for item in doc.edges:
            self._session.add(
                MapEdge(
                    id=uuid.uuid4(),
                    from_node_id=nodes[item.from_node_key].id,
                    to_node_id=nodes[item.to_node_key].id,
                    distance_m=item.distance_m,
                    edge_type=item.edge_type,
                    accessible=item.accessible,
                    avg_seconds=item.avg_seconds,
                )
            )
        await self._session.flush()
        return mall
