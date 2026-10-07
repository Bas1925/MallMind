"""Declarative base + shared column mixins.

Design notes
------------
- `naming_convention` on MetaData gives Alembic deterministic names for
  indexes and constraints. Without this, auto-generated names change
  across Postgres versions and migrations become fragile.
- `TimestampMixin` is intentionally lightweight: just `created_at` and
  `updated_at`. We will add `deleted_at` only when soft-delete becomes
  a real requirement.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    """Adds `created_at` / `updated_at` to a model.

    Server-side defaults (`now()`) chosen over Python-side `datetime.utcnow`
    so timestamps are consistent across clients and timezones.
    """

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
