"""Initial MallMind schema.

Creates the six MVP tables (malls, floors, categories, locations,
map_nodes, map_edges) and the two Postgres ENUM types the graph needs.
Also installs pgvector + pg_trgm so later phases can add vector columns
and trigram indexes without a second schema-wide bootstrap.

Why hand-written and not autogenerate?

Postgres ENUMs are the classic Alembic autogenerate blind-spot: `op.create_table`
with `SAEnum(...)` tries to drop/recreate the type during every unrelated migration
in a long chain. Hand-writing the first migration lets us declare the enum once with
an explicit name, create tables that merely *reference* it, and never have to
revisit the enum unless we add a value. See ADR-006.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-06
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# ---------------------------------------------------------------------------
# Enum definitions (declared once, reused in multiple tables)
# ---------------------------------------------------------------------------

NODE_TYPE_VALUES = (
    "hallway_junction",
    "store_anchor",
    "entrance",
    "exit",
    "bathroom",
    "atm",
    "elevator_landing",
    "stairs_landing",
    "escalator_up_landing",
    "escalator_down_landing",
    "info_desk",
)

EDGE_TYPE_VALUES = (
    "hallway",
    "stairs",
    "elevator",
    "escalator_up",
    "escalator_down",
)


def upgrade() -> None:
    # ----- Extensions ------------------------------------------------------
    # Idempotent. Needed by:
    #   pg_trgm  — Phase 4 (hybrid text search; GIN trigram index)
    #   vector   — Phase 5 (RAG embeddings)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ----- Enum types ------------------------------------------------------
    node_type_enum = postgresql.ENUM(*NODE_TYPE_VALUES, name="node_type", create_type=False)
    edge_type_enum = postgresql.ENUM(*EDGE_TYPE_VALUES, name="edge_type", create_type=False)
    node_type_enum.create(op.get_bind(), checkfirst=True)
    edge_type_enum.create(op.get_bind(), checkfirst=True)

    # ----- malls -----------------------------------------------------------
    op.create_table(
        "malls",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column("slug", sa.String(length=64), nullable=False, unique=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=False),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # ----- floors ----------------------------------------------------------
    op.create_table(
        "floors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "mall_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("malls.id", ondelete="RESTRICT", name="fk_floors_mall_id_malls"),
            nullable=False,
        ),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.UniqueConstraint("mall_id", "level", name="uq_floors_mall_id_level"),
    )
    op.create_index("ix_floors_mall_id", "floors", ["mall_id"])

    # ----- categories ------------------------------------------------------
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("slug", sa.String(length=64), nullable=False, unique=True),
        sa.Column("name_en", sa.String(length=128), nullable=False),
        sa.Column("name_he", sa.String(length=128), nullable=False),
        sa.Column("name_ar", sa.String(length=128), nullable=False),
    )

    # ----- locations -------------------------------------------------------
    op.create_table(
        "locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "mall_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("malls.id", ondelete="RESTRICT", name="fk_locations_mall_id_malls"),
            nullable=False,
        ),
        sa.Column(
            "floor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("floors.id", ondelete="RESTRICT", name="fk_locations_floor_id_floors"),
            nullable=False,
        ),
        sa.Column(
            "category_id",
            sa.Integer(),
            sa.ForeignKey(
                "categories.id",
                ondelete="RESTRICT",
                name="fk_locations_category_id_categories",
            ),
            nullable=False,
        ),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "wheelchair_accessible",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=False),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("mall_id", "slug", name="uq_locations_mall_id_slug"),
    )
    op.create_index("ix_locations_mall_id", "locations", ["mall_id"])
    op.create_index("ix_locations_floor_id", "locations", ["floor_id"])
    op.create_index("ix_locations_category_id", "locations", ["category_id"])

    # ----- map_nodes -------------------------------------------------------
    op.create_table(
        "map_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "floor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("floors.id", ondelete="RESTRICT", name="fk_map_nodes_floor_id_floors"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "locations.id",
                ondelete="SET NULL",
                name="fk_map_nodes_location_id_locations",
            ),
            nullable=True,
            unique=True,
        ),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("node_type", node_type_enum, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=False),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_map_nodes_floor_id", "map_nodes", ["floor_id"])

    # ----- map_edges -------------------------------------------------------
    op.create_table(
        "map_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "from_node_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "map_nodes.id",
                ondelete="RESTRICT",
                name="fk_map_edges_from_node_id_map_nodes",
            ),
            nullable=False,
        ),
        sa.Column(
            "to_node_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "map_nodes.id",
                ondelete="RESTRICT",
                name="fk_map_edges_to_node_id_map_nodes",
            ),
            nullable=False,
        ),
        sa.Column("distance_m", sa.Float(), nullable=False),
        sa.Column("edge_type", edge_type_enum, nullable=False),
        sa.Column("accessible", sa.Boolean(), nullable=False),
        sa.Column("avg_seconds", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=False),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("from_node_id", "to_node_id", name="uq_map_edges_from_to"),
        sa.CheckConstraint("distance_m >= 0.0", name="ck_map_edges_distance_non_negative"),
        sa.CheckConstraint("avg_seconds > 0.0", name="ck_map_edges_avg_seconds_positive"),
        sa.CheckConstraint("from_node_id <> to_node_id", name="ck_map_edges_no_self_loop"),
    )
    op.create_index("ix_map_edges_from_node_id", "map_edges", ["from_node_id"])
    op.create_index("ix_map_edges_to_node_id", "map_edges", ["to_node_id"])


def downgrade() -> None:
    op.drop_index("ix_map_edges_to_node_id", table_name="map_edges")
    op.drop_index("ix_map_edges_from_node_id", table_name="map_edges")
    op.drop_table("map_edges")
    op.drop_index("ix_map_nodes_floor_id", table_name="map_nodes")
    op.drop_table("map_nodes")
    op.drop_index("ix_locations_category_id", table_name="locations")
    op.drop_index("ix_locations_floor_id", table_name="locations")
    op.drop_index("ix_locations_mall_id", table_name="locations")
    op.drop_table("locations")
    op.drop_table("categories")
    op.drop_index("ix_floors_mall_id", table_name="floors")
    op.drop_table("floors")
    op.drop_table("malls")

    # Enum types outlive their tables; drop them last.
    postgresql.ENUM(name="edge_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="node_type").drop(op.get_bind(), checkfirst=True)
    # Extensions are intentionally NOT dropped — they may be used by other
    # objects outside Alembic's scope.
