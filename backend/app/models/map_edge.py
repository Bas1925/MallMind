"""`MapEdge` model — a directed connection between two MapNodes."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .enums import EdgeType, pg_enum_values

if TYPE_CHECKING:
    from .map_node import MapNode


class MapEdge(Base, TimestampMixin):
    """
    DIRECTED edge. Bidirectional connections are modelled as two edges
    (A→B and B→A). See ADR-008.
    """

    __tablename__ = "map_edges"
    __table_args__ = (
        UniqueConstraint("from_node_id", "to_node_id", name="uq_map_edges_from_to"),
        CheckConstraint("distance_m >= 0.0", name="distance_non_negative"),
        CheckConstraint("avg_seconds > 0.0", name="avg_seconds_positive"),
        CheckConstraint("from_node_id <> to_node_id", name="no_self_loop"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("map_nodes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    to_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("map_nodes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    distance_m: Mapped[float] = mapped_column(Float, nullable=False)
    edge_type: Mapped[EdgeType] = mapped_column(
        SAEnum(
            EdgeType,
            name="edge_type",
            native_enum=True,
            create_constraint=False,
            values_callable=pg_enum_values,
        ),
        nullable=False,
    )
    accessible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    avg_seconds: Mapped[float] = mapped_column(Float, nullable=False)

    from_node: Mapped[MapNode] = relationship(
        "MapNode",
        back_populates="outgoing_edges",
        foreign_keys=[from_node_id],
    )
    to_node: Mapped[MapNode] = relationship(
        "MapNode",
        back_populates="incoming_edges",
        foreign_keys=[to_node_id],
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<MapEdge {self.from_node_id} -> {self.to_node_id} "
            f"type={self.edge_type.value} dist={self.distance_m}m>"
        )
