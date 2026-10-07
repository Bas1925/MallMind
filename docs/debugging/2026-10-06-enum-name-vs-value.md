# 2026-10-06 — SQLAlchemy bound enum *names* to a Postgres ENUM of *values*

**Severity:** high (blocked all seed inserts)
**Time to find:** first real `alembic upgrade` + seed against PostgreSQL 16
**Area:** persistence / Alembic / enums

## Symptom

`python -m app.seed` failed after a successful `alembic upgrade head`:

```
asyncpg.exceptions.InvalidTextRepresentationError:
invalid input value for enum node_type: "HALLWAY_JUNCTION"
```

The migration created `node_type` with labels like `hallway_junction`. The INSERT bound `HALLWAY_JUNCTION` — the Python member name.

## Hypothesis path

1. **Seed builder used the wrong string.** Ruled out: `NodeType.HALLWAY_JUNCTION` is a `StrEnum` whose `.value` is `hallway_junction`.
2. **The Postgres type was created from names.** Ruled out: `psql` / `SELECT enumlabel FROM pg_enum` shows lowercase values matching the hand-written migration.
3. **SQLAlchemy native ENUM default is member name.** Confirmed. `SAEnum(NodeType, native_enum=True)` binds `.name` unless `values_callable` returns `.value`.

## Root cause

SQLAlchemy's PostgreSQL ENUM adapter defaults to enum **names**. Our Python members are `HALLWAY_JUNCTION`; our Postgres labels are `hallway_junction`. This was invisible until the first insert against a real database — unit tests never flushed a `MapNode` to Postgres, and seed validation is in-memory.

Switching `NodeType` to `enum.StrEnum` (ruff UP042) did not change this; StrEnum is still a name/value pair, and SQLAlchemy still prefers the name for native enums.

## Fix

`values_callable=pg_enum_values` on both `node_type` and `edge_type` columns, where `pg_enum_values` returns `[m.value for m in enum_cls]`.

Regression test: insert `NodeType.HALLWAY_JUNCTION` and `SELECT node_type::text` equals `hallway_junction`.

## Lesson

A Python `StrEnum` is not automatically "the string Postgres wants." Native Postgres ENUMs and Python enums are two vocabularies. Bind `.value` explicitly, and test the round-trip against real PostgreSQL — SQLite and in-memory validation will not catch this.
