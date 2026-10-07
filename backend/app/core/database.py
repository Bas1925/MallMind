"""Async SQLAlchemy engine and session factory.

Design notes
------------
- `pool_pre_ping=True` costs one round-trip per checkout but detects stale
  connections before they explode mid-request. For a small-pool API this
  trade-off is almost always worth it.
- `expire_on_commit=False` means ORM objects remain usable after commit —
  important for async handlers that return objects after a flush.
- The engine is a module-level singleton. Tests that need isolation
  construct their own engine via a fixture (see `tests/conftest.py`).
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import settings

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yields a session scoped to a single request."""
    async with SessionLocal() as session:
        yield session
