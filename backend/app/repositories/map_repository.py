"""Read model for the indoor map. Coordinates match the routing graph."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Category, Floor, Location, Mall, MapEdge, MapNode


class MapRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_mall_by_slug(self, slug: str) -> Mall | None:
        return await self._session.scalar(select(Mall).where(Mall.slug == slug))

    async def list_floors(self, mall_id: object) -> list[Floor]:
        result = await self._session.scalars(
            select(Floor).where(Floor.mall_id == mall_id).order_by(Floor.display_order)
        )
        return list(result.all())

    async def list_nodes(self, floor_ids: list[object]) -> list[MapNode]:
        if not floor_ids:
            return []
        result = await self._session.scalars(select(MapNode).where(MapNode.floor_id.in_(floor_ids)))
        return list(result.all())

    async def list_edges(self, node_ids: list[object]) -> list[MapEdge]:
        if not node_ids:
            return []
        result = await self._session.scalars(
            select(MapEdge).where(MapEdge.from_node_id.in_(node_ids))
        )
        return list(result.all())

    async def list_locations(self, mall_id: object) -> list[Location]:
        result = await self._session.scalars(
            select(Location)
            .options(
                selectinload(Location.category),
                selectinload(Location.floor),
                selectinload(Location.anchor_node),
            )
            .where(Location.mall_id == mall_id, Location.is_active.is_(True))
            .order_by(Location.name)
        )
        return list(result.all())

    async def search_locations(self, mall_id: object, query: str) -> list[Location]:
        pattern = f"%{query.strip()}%"
        result = await self._session.scalars(
            select(Location)
            .join(Location.category)
            .options(
                selectinload(Location.category),
                selectinload(Location.floor),
                selectinload(Location.anchor_node),
            )
            .where(
                Location.mall_id == mall_id,
                Location.is_active.is_(True),
                or_(
                    Location.name.ilike(pattern),
                    Location.slug.ilike(pattern),
                    Location.description.ilike(pattern),
                    Category.slug.ilike(pattern),
                    Category.name_en.ilike(pattern),
                ),
            )
            .order_by(Location.name)
            .limit(30)
        )
        return list(result.all())
