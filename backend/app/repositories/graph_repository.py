"""Load the mall navigation graph from PostgreSQL."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Floor, Location, Mall, MapEdge, MapNode
from app.routing.types import GraphEdge, GraphNode, MallGraph


class GraphRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def load_mall_graph(self, mall_slug: str = "nova-mall") -> MallGraph:
        mall = await self._session.scalar(select(Mall).where(Mall.slug == mall_slug))
        if mall is None:
            return MallGraph(nodes={}, outgoing={})
        floors = (await self._session.scalars(select(Floor).where(Floor.mall_id == mall.id))).all()
        if not floors:
            return MallGraph(nodes={}, outgoing={})
        floor_by_id = {f.id: f for f in floors}
        nodes_orm = (
            await self._session.scalars(
                select(MapNode).where(MapNode.floor_id.in_([f.id for f in floors]))
            )
        ).all()
        node_ids = [n.id for n in nodes_orm]
        if not node_ids:
            return MallGraph(nodes={}, outgoing={})
        edges_orm = (
            await self._session.scalars(select(MapEdge).where(MapEdge.from_node_id.in_(node_ids)))
        ).all()
        nodes = {
            n.id: GraphNode(
                id=n.id,
                floor_id=n.floor_id,
                floor_level=floor_by_id[n.floor_id].level,
                x=n.x,
                y=n.y,
                node_type=n.node_type,
                location_id=n.location_id,
                key=None,
            )
            for n in nodes_orm
        }
        outgoing: dict[uuid.UUID, list[GraphEdge]] = {nid: [] for nid in nodes}
        for e in edges_orm:
            ge = GraphEdge(
                id=e.id,
                from_id=e.from_node_id,
                to_id=e.to_node_id,
                distance_m=e.distance_m,
                avg_seconds=e.avg_seconds,
                accessible=e.accessible,
                edge_type=e.edge_type,
            )
            outgoing[e.from_node_id].append(ge)
        by_location_id = {n.location_id: n.id for n in nodes.values() if n.location_id is not None}
        return MallGraph(nodes=nodes, outgoing=outgoing, by_location_id=by_location_id)

    async def get_location(self, location_id: object) -> Location | None:
        return await self._session.scalar(
            select(Location)
            .options(selectinload(Location.anchor_node), selectinload(Location.floor))
            .where(Location.id == location_id)
        )
