"""Alembic environment.

Design notes
------------
- We use the SYNC `psycopg` driver for migrations. The app runs async with
  `asyncpg`, but Alembic's migration context is sync-only and spawning an
  async event loop just for migrations is unnecessary complexity.
- `DATABASE_URL` from env (same variable the app uses) is translated:
  `postgresql+asyncpg://…` → `postgresql+psycopg://…`.
- `compare_type=True` so autogenerate catches column type changes.
- `compare_server_default=True` so autogenerate catches default changes.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _resolve_sync_db_url() -> str:
    """Translate the app's async DSN into the sync one Alembic needs."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Alembic needs it to run migrations. "
            "Example: postgresql+asyncpg://mallmind:mallmind_dev_only@localhost:5432/mallmind"
        )
    # The app uses asyncpg; Alembic uses sync psycopg.
    return url.replace("+asyncpg", "+psycopg")


def run_migrations_offline() -> None:
    """Emit SQL to stdout — useful for dry-runs and `alembic upgrade head --sql`."""
    url = _resolve_sync_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB."""
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = _resolve_sync_db_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
