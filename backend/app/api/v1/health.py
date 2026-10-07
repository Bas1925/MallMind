"""Health endpoint.

Returns:
    200 OK            with status="ok",       db="ok"   when Postgres responds
    503 Unavailable   with status="degraded", db="down" when Postgres doesn't

This matters because:
- Container orchestrators (Docker, Kubernetes) use the HTTP status to decide
  whether a container is healthy. If we always returned 200, a dead-DB
  backend would silently stay in rotation.
- Humans (and Grafana) can read the JSON body for a quick summary.

The response always has the same shape, which keeps clients simple.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.database import get_session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str  # "ok" | "degraded"
    db: str  # "ok" | "down"
    version: str


@router.get("/health", response_model=HealthResponse)
async def health(db: AsyncSession = Depends(get_session)) -> JSONResponse:
    """
    Health check that MUST NEVER raise.

    We catch `Exception` on purpose (and tell ruff that). A health endpoint
    that 500s is strictly worse than one that reports "degraded": container
    orchestrators treat 500 as a transient fault but 503 as "this instance
    is bad, stop sending it traffic." See docs/debugging/2026-10-05-health-
    endpoint-missed-connectionrefused.md for the real bug that drove this.
    """
    db_ok = True
    try:
        # Cheapest possible query — proves (a) the pool can hand us a
        # connection and (b) the server actually answered.
        await db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — see docstring
        db_ok = False
        logger.warning("Health check: DB probe failed (%s): %s", type(exc).__name__, exc)

    payload = HealthResponse(
        status="ok" if db_ok else "degraded",
        db="ok" if db_ok else "down",
        version=settings.app_version,
    )
    http_status = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=payload.model_dump(), status_code=http_status)
