"""Helpers for tests that need a real PostgreSQL.

SQLite is not used. If Postgres is unreachable, callers skip.
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER_DSN = "postgresql+asyncpg://test:test@localhost:5432/test"


def database_url() -> str:
    return os.environ.get("DATABASE_URL", PLACEHOLDER_DSN)


def is_placeholder_url(url: str) -> bool:
    return url == PLACEHOLDER_DSN


def postgres_reachable(url: str | None = None) -> bool:
    url = url or database_url()
    if is_placeholder_url(url):
        return False
    sync_url = url.replace("+asyncpg", "+psycopg").replace("postgresql+psycopg://", "postgresql://")
    try:
        with psycopg.connect(sync_url, connect_timeout=3) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:  # noqa: BLE001 — skip-check must never crash the suite
        return False


def alembic_upgrade_head() -> None:
    from alembic.config import Config

    from alembic import command

    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    command.upgrade(cfg, "head")
