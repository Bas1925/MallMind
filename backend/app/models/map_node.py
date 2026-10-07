"""`MapNode` model — a vertex in the navigation graph."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .enums import NodeType, pg_enum_values

if TYPE_CHECKING:
    from .floor import Floor
    from .location import Location
    from .map_edge import MapEdge


class MapNode(Base, TimestampMixin):
    __tablename__ = "map_nodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    floor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("floors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Nullable: most nodes (hallway junctions, landings) have no location.
    # Unique: in Phase 1 at most one node anchors a given location.
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    # Floor-local coordinates in abstract units (see ADR-007).
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    node_type: Mapped[NodeType] = mapped_column(
        SAEnum(
            NodeType,
            name="node_type",
            native_enum=True,
            create_constraint=False,
            values_callable=pg_enum_values,
        ),
        nullable=False,
    )

    floor: Mapped[Floor] = relationship("Floor", back_populates="nodes")
    location: Mapped[Location | None] = relationship("Location", back_populates="anchor_node")

    outgoing_edges: Mapped[list[MapEdge]] = relationship(
        "MapEdge",
        back_populates="from_node",
        foreign_keys="MapEdge.from_node_id",
    )
    incoming_edges: Mapped[list[MapEdge]] = relationship(
        "MapEdge",
        back_populates="to_node",
        foreign_keys="MapEdge.to_node_id",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MapNode id={self.id} type={self.node_type.value} ({self.x},{self.y})>"
