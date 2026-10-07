"""FastAPI application entrypoint.

Design notes
------------
- `create_app()` is a factory so tests can build fresh instances without
  reusing module-level global state.
- `lifespan` performs a one-time DB probe at startup. A failure is logged
  but does NOT prevent startup: we want the service to come up and report
  "degraded" via /health so operators can see it, instead of crash-looping
  silently.
- CORS is configured from settings so dev / staging / prod can differ
  without code changes.
- Routers are mounted under /api/v1 — versioning is cheap now, painful later.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .api.v1 import assistant as assistant_router
from .api.v1 import health as health_router
from .api.v1 import map as map_router
from .api.v1 import navigation as navigation_router
from .api.v1 import search as search_router
from .core.config import settings
from .core.database import engine

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "Starting %s v%s (environment=%s)",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )
    # Startup DB probe. Non-fatal — see module docstring.
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connectivity verified at startup")
    except Exception as exc:  # noqa: BLE001 — intentional broad catch at bootstrap
        logger.warning(
            "Database unreachable at startup (%s); service will come up "
            "and report degraded via /health",
            exc,
        )
    yield
    logger.info("Shutting down, disposing database engine")
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        allow_credentials=False,
    )
    app.include_router(health_router.router, prefix="/api/v1")
    app.include_router(navigation_router.router, prefix="/api/v1")
    app.include_router(map_router.router, prefix="/api/v1")
    app.include_router(search_router.router, prefix="/api/v1")
    app.include_router(assistant_router.router, prefix="/api/v1")
    return app


app = create_app()
