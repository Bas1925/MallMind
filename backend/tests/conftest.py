"""Shared pytest fixtures.

Phase 0b note
-------------
We only have one trivial endpoint right now. Fixtures here are deliberately
minimal; richer fixtures (seeded test DB, isolated per-test transactions,
service-layer fakes) will arrive in Phase 1 when there is real behaviour
to test.

Testing strategy
----------------
- `app` : a FastAPI instance built per-test, so modifying one test's app
          state cannot leak into another.
- `client` : an `httpx.AsyncClient` wired directly to the ASGI app via
             `ASGITransport`. This bypasses the network entirely, so tests
             are fast and don't need a running uvicorn.
"""

from __future__ import annotations

# Phase 0b setup: provide a dummy DATABASE_URL *before* app modules are
# imported, so pydantic-settings doesn't fail validation in CI envs that
# forget to set it. Tests that need a real DB will supply a real URL and
# an override fixture.
import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://test:test@localhost:5432/test",
)
# Search tests must not download an embedding model or call a paid API.
os.environ["EMBEDDING_PROVIDER"] = "none"
os.environ["LLM_API_KEY"] = ""

from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_session
from app.core.ratelimit import reset_rate_limits_for_tests
from app.main import create_app
from app.seed.nova_mall import build_nova_mall
from app.services.seed_service import SeedService
from tests.db_support import alembic_upgrade_head, database_url, postgres_reachable


@pytest.fixture(autouse=True)
def _reset_rate_limits() -> None:
    reset_rate_limits_for_tests()


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def seeded_session() -> AsyncIterator[AsyncSession]:
    url = database_url()
    if not postgres_reachable(url):
        pytest.skip("PostgreSQL is not reachable")
    alembic_upgrade_head()
    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        async with session.begin():
            await SeedService(session).apply(build_nova_mall(), force=True)
        yield session
        await session.rollback()
    await engine.dispose()


@pytest.fixture
async def api_client(app: FastAPI, seeded_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def _override() -> AsyncIterator[AsyncSession]:
        yield seeded_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
