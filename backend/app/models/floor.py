"""`Floor` model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .location import Location
    from .mall import Mall
    from .map_node import MapNode


class Floor(Base):
    __tablename__ = "floors"
    __table_args__ = (UniqueConstraint("mall_id", "level", name="uq_floors_mall_id_level"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mall_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("malls.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)

    mall: Mapped[Mall] = relationship("Mall", back_populates="floors")
    locations: Mapped[list[Location]] = relationship(
        "Location",
        back_populates="floor",
    )
    nodes: Mapped[list[MapNode]] = relationship(
        "MapNode",
        back_populates="floor",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Floor level={self.level} name={self.name!r}>"
