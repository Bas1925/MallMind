"""SQLAlchemy ORM models for MallMind.

Import every model here so `Base.metadata` is fully populated when
Alembic reflects it. Missing an import = missing a table in autogenerate.
"""

from .base import Base
from .category import Category
from .enums import EdgeType, NodeType
from .floor import Floor
from .location import Location
from .location_document import LocationDocument
from .mall import Mall
from .map_edge import MapEdge
from .map_node import MapNode

__all__ = [
    "Base",
    "Category",
    "EdgeType",
    "Floor",
    "Location",
    "LocationDocument",
    "Mall",
    "MapEdge",
    "MapNode",
    "NodeType",
]
