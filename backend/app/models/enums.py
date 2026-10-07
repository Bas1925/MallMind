"""Enums used by the graph models.

Keep these in a dedicated module so Alembic auto-detects additions,
removals, and renames across the schema in one place.

NOTE on Postgres enum migrations
--------------------------------
Alembic's autogenerate does NOT reliably create / drop / alter Postgres
ENUM types. Every enum change requires a human-written migration op
(`op.execute("ALTER TYPE … ADD VALUE …")`). See ADR-006.
"""

from __future__ import annotations

import enum


def pg_enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    """Persist Python Enum *values* to Postgres, not member names.

    Native Postgres ENUMs in our migrations are lowercase (`hallway_junction`).
    SQLAlchemy's default is to bind the member name (`HALLWAY_JUNCTION`), which
    asyncpg rejects. See docs/debugging/2026-10-06-enum-name-vs-value.md.
    """
    return [member.value for member in enum_cls]


class NodeType(enum.StrEnum):
    HALLWAY_JUNCTION = "hallway_junction"
    STORE_ANCHOR = "store_anchor"
    ENTRANCE = "entrance"
    EXIT = "exit"
    BATHROOM = "bathroom"
    ATM = "atm"
    ELEVATOR_LANDING = "elevator_landing"
    STAIRS_LANDING = "stairs_landing"
    ESCALATOR_UP_LANDING = "escalator_up_landing"
    ESCALATOR_DOWN_LANDING = "escalator_down_landing"
    INFO_DESK = "info_desk"


class EdgeType(enum.StrEnum):
    HALLWAY = "hallway"
    STAIRS = "stairs"
    ELEVATOR = "elevator"
    ESCALATOR_UP = "escalator_up"
    ESCALATOR_DOWN = "escalator_down"


# Which node types are vertical-connector landings.
VERTICAL_LANDING_NODE_TYPES: frozenset[NodeType] = frozenset(
    {
        NodeType.ELEVATOR_LANDING,
        NodeType.STAIRS_LANDING,
        NodeType.ESCALATOR_UP_LANDING,
        NodeType.ESCALATOR_DOWN_LANDING,
    }
)

# Which edge types cross floors.
VERTICAL_EDGE_TYPES: frozenset[EdgeType] = frozenset(
    {
        EdgeType.STAIRS,
        EdgeType.ELEVATOR,
        EdgeType.ESCALATOR_UP,
        EdgeType.ESCALATOR_DOWN,
    }
)
