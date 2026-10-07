"""`Mall` model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .floor import Floor
    from .location import Location


class Mall(Base, TimestampMixin):
    __tablename__ = "malls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, server_default="UTC")

    floors: Mapped[list[Floor]] = relationship(
        "Floor",
        back_populates="mall",
        cascade="all, delete-orphan",
        order_by="Floor.display_order",
    )
    locations: Mapped[list[Location]] = relationship(
        "Location",
        back_populates="mall",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug only
        return f"<Mall slug={self.slug!r} name={self.name!r}>"
