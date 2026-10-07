"""`Location` model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .category import Category
    from .floor import Floor
    from .mall import Mall
    from .map_node import MapNode


class Location(Base, TimestampMixin):
    __tablename__ = "locations"
    __table_args__ = (UniqueConstraint("mall_id", "slug", name="uq_locations_mall_id_slug"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mall_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("malls.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    floor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("floors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    wheelchair_accessible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    mall: Mapped[Mall] = relationship("Mall", back_populates="locations")
    floor: Mapped[Floor] = relationship("Floor", back_populates="locations")
    category: Mapped[Category] = relationship("Category", back_populates="locations")
    # Reverse of MapNode.location_id; at most one node due to UNIQUE on
    # map_nodes.location_id. `uselist=False` makes SQLAlchemy expose a
    # scalar instead of a one-element list.
    anchor_node: Mapped[MapNode | None] = relationship(
        "MapNode",
        back_populates="location",
        uselist=False,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Location slug={self.slug!r} name={self.name!r}>"
