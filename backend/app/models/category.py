"""`Category` model.

Flat (non-hierarchical) by design — see docs/02-phase-1-design.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .location import Location


class Category(Base):
    __tablename__ = "categories"

    # Small serial integer PK — categories are a short enum-ish list.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(128), nullable=False)
    name_he: Mapped[str] = mapped_column(String(128), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(128), nullable=False)

    locations: Mapped[list[Location]] = relationship("Location", back_populates="category")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Category slug={self.slug!r}>"
