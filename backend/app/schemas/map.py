"""Pydantic payloads for the indoor-map API.

This is a *read model* for the frontend. It uses the same (x, y, floor)
coordinates as the routing graph. The browser must not invent a second map.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class MapMall(BaseModel):
    id: uuid.UUID
    slug: str
    name: str


class MapFloor(BaseModel):
    id: uuid.UUID
    level: int
    name: str
    display_order: int


class MapLocation(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    category_slug: str
    category_name: str
    floor_id: uuid.UUID
    floor_level: int
    floor_name: str
    anchor_node_id: uuid.UUID | None
    x: float | None
    y: float | None
    node_type: str | None
    wheelchair_accessible: bool


class MapNodeOut(BaseModel):
    id: uuid.UUID
    floor_id: uuid.UUID
    floor_level: int
    x: float
    y: float
    node_type: str
    location_id: uuid.UUID | None


class MapEdgeOut(BaseModel):
    id: uuid.UUID
    from_node_id: uuid.UUID
    to_node_id: uuid.UUID
    from_floor_level: int
    to_floor_level: int
    edge_type: str
    accessible: bool


class MallMapResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mall: MapMall
    floors: list[MapFloor]
    locations: list[MapLocation]
    nodes: list[MapNodeOut]
    edges: list[MapEdgeOut]


class LocationSearchResponse(BaseModel):
    results: list[MapLocation] = Field(default_factory=list)
