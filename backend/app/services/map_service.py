"""Assemble the indoor-map read model. No routing here."""

from __future__ import annotations

from app.models import Location
from app.repositories.map_repository import MapRepository
from app.schemas.map import (
    MallMapResponse,
    MapEdgeOut,
    MapFloor,
    MapLocation,
    MapMall,
    MapNodeOut,
)


class MapNotFoundError(Exception):
    pass


_SEARCH_ALIASES = {
    "bathroom": "restroom",
    "bathrooms": "restroom",
    "toilet": "restroom",
    "toilets": "restroom",
    "wc": "restroom",
}


class MapService:
    def __init__(self, repo: MapRepository) -> None:
        self._repo = repo

    async def get_map(self, slug: str) -> MallMapResponse:
        mall = await self._repo.get_mall_by_slug(slug)
        if mall is None:
            raise MapNotFoundError(slug)
        floors = await self._repo.list_floors(mall.id)
        floor_ids = [f.id for f in floors]
        nodes = await self._repo.list_nodes(floor_ids)
        node_by_id = {n.id: n for n in nodes}
        floor_by_id = {f.id: f for f in floors}
        edges = await self._repo.list_edges([n.id for n in nodes])
        locations = await self._repo.list_locations(mall.id)
        return MallMapResponse(
            mall=MapMall(id=mall.id, slug=mall.slug, name=mall.name),
            floors=[
                MapFloor(id=f.id, level=f.level, name=f.name, display_order=f.display_order)
                for f in floors
            ],
            locations=[_location_out(loc) for loc in locations],
            nodes=[
                MapNodeOut(
                    id=n.id,
                    floor_id=n.floor_id,
                    floor_level=floor_by_id[n.floor_id].level,
                    x=n.x,
                    y=n.y,
                    node_type=n.node_type.value,
                    location_id=n.location_id,
                )
                for n in nodes
            ],
            edges=[
                MapEdgeOut(
                    id=e.id,
                    from_node_id=e.from_node_id,
                    to_node_id=e.to_node_id,
                    from_floor_level=floor_by_id[node_by_id[e.from_node_id].floor_id].level,
                    to_floor_level=floor_by_id[node_by_id[e.to_node_id].floor_id].level,
                    edge_type=e.edge_type.value,
                    accessible=e.accessible,
                )
                for e in edges
                if e.from_node_id in node_by_id and e.to_node_id in node_by_id
            ],
        )

    async def search(self, slug: str, query: str) -> list[MapLocation]:
        mall = await self._repo.get_mall_by_slug(slug)
        if mall is None:
            raise MapNotFoundError(slug)
        trimmed = query.strip()
        if trimmed == "":
            locations = await self._repo.list_locations(mall.id)
        else:
            locations = await self._repo.search_locations(mall.id, trimmed)
            alias = _SEARCH_ALIASES.get(trimmed.lower())
            if alias is not None:
                extra = await self._repo.search_locations(mall.id, alias)
                seen = {loc.id for loc in locations}
                locations = locations + [loc for loc in extra if loc.id not in seen]
        return [_location_out(loc) for loc in locations]


def _location_out(loc: Location) -> MapLocation:
    anchor = loc.anchor_node
    return MapLocation(
        id=loc.id,
        slug=loc.slug,
        name=loc.name,
        description=loc.description,
        category_slug=loc.category.slug,
        category_name=loc.category.name_en,
        floor_id=loc.floor_id,
        floor_level=loc.floor.level,
        floor_name=loc.floor.name,
        anchor_node_id=anchor.id if anchor is not None else None,
        x=anchor.x if anchor is not None else None,
        y=anchor.y if anchor is not None else None,
        node_type=anchor.node_type.value if anchor is not None else None,
        wheelchair_accessible=loc.wheelchair_accessible,
    )
