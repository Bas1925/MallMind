"""Tests for the /health endpoint.

What this test actually verifies
--------------------------------
The health endpoint must:
  1. Always respond (never 500) even if the database is unreachable.
  2. Return a well-defined JSON shape: {status, db, version}.
  3. Signal degradation via HTTP status: 200 when DB is up, 503 when down.

What this test deliberately does NOT verify
-------------------------------------------
It does not assert specific DB status. In CI we point at a real Postgres
and expect 200; locally without a DB we accept 503. A dedicated
integration test (Phase 1) will pin the "DB up → 200" expectation.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_responds_with_expected_shape(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    # Must be one of our two documented states; never 500.
    assert response.status_code in (200, 503), (
        f"health endpoint returned unexpected status {response.status_code}; body={response.text}"
    )

    body = response.json()
    assert set(body.keys()) == {"status", "db", "version"}
    assert body["status"] in ("ok", "degraded")
    assert body["db"] in ("ok", "down")
    assert isinstance(body["version"], str) and body["version"]


@pytest.mark.asyncio
async def test_health_status_consistent_with_db_state(client: AsyncClient) -> None:
    """The two fields must agree: ok+ok on 200, degraded+down on 503."""
    response = await client.get("/api/v1/health")
    body = response.json()

    if response.status_code == 200:
        assert body == {"status": "ok", "db": "ok", "version": body["version"]}
    else:
        assert response.status_code == 503
        assert body == {"status": "degraded", "db": "down", "version": body["version"]}
