"""Seed-document Pydantic schemas.

These describe the on-disk JSON format for a mall seed. The seed uses
STRING KEYS (`floor_key`, `node_key`, etc.) instead of UUIDs so a human
can author the file by hand. The loader resolves keys to UUIDs during
insert.

Pydantic performs *structural* validation here (required fields, type
checks, basic numeric bounds). Cross-reference and topology checks live
in `app.seed.validator` so that one layer can run without the other.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import EdgeType, NodeType

Key = str  # alias — just means "a human-readable identifier within the seed"


class SeedCategory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(min_length=1, max_length=64)
    name_en: str
    name_he: str
    name_ar: str


class SeedFloor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: Key = Field(min_length=1)
    level: int
    name: str
    display_order: int


class SeedLocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(min_length=1, max_length=64)
    name: str
    category_slug: str
    floor_key: Key
    anchor_node_key: Key
    description: str | None = None
    wheelchair_accessible: bool = True


class SeedNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: Key = Field(min_length=1)
    floor_key: Key
    node_type: NodeType
    x: float
    y: float
    # Optional convenience — if set, must match a location's `anchor_node_key`.
    # Primarily documentation; the loader uses location.anchor_node_key.
    location_slug: str | None = None


class SeedEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_node_key: Key
    to_node_key: Key
    distance_m: float
    edge_type: EdgeType
    accessible: bool
    avg_seconds: float

    @field_validator("distance_m")
    @classmethod
    def _distance_non_negative(cls, v: float) -> float:
        if v < 0.0:
            raise ValueError("distance_m must be >= 0.0")
        return v

    @field_validator("avg_seconds")
    @classmethod
    def _seconds_positive(cls, v: float) -> float:
        if v <= 0.0:
            raise ValueError("avg_seconds must be > 0.0")
        return v


class SeedMall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(min_length=1, max_length=64)
    name: str
    city: str | None = None
    timezone: str = "UTC"


class SeedDocument(BaseModel):
    """The full seed-file schema."""

    model_config = ConfigDict(extra="forbid")

    mall: SeedMall
    floors: list[SeedFloor]
    categories: list[SeedCategory]
    locations: list[SeedLocation]
    nodes: list[SeedNode]
    edges: list[SeedEdge]
