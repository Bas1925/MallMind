"""Programmatic definition of the NOVA Mall seed.

Why Python instead of a hand-written JSON file?
  A 3-floor hallway grid plus vertical shafts is ~90 nodes and ~200 directed
  edges. Hand-authoring that is how duplicate edges and missed reverse
  hallways sneak in. The builder emits a `SeedDocument`; the validator still
  treats it as untrusted input (tests mutate copies to prove it can fail).

Coordinate system: floor-local metres-like units, origin at the south-west
corner. See ADR-007. The hallway grid is identical on every floor so
vertical shafts can stack at the same (x, y).
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from itertools import pairwise

from app.models.enums import EdgeType, NodeType
from app.schemas.seed import (
    SeedCategory,
    SeedDocument,
    SeedEdge,
    SeedFloor,
    SeedLocation,
    SeedMall,
    SeedNode,
)

WALK_MPS = 1.25  # typical indoor walking speed used to derive avg_seconds

# Hallway grid — 6 east-west columns by 3 north-south rows per floor.
XS: tuple[int, ...] = (10, 30, 50, 70, 90, 110)
YS: tuple[int, ...] = (10, 40, 70)

FLOOR_GROUND = "ground"
FLOOR_L1 = "l1"
FLOOR_L2 = "l2"
FLOOR_KEYS: tuple[str, ...] = (FLOOR_GROUND, FLOOR_L1, FLOOR_L2)

# Vertical shafts (stacked at the same (x, y) on every floor).
ELEVATOR_XY = (50.0, 48.0)
STAIRS_XY = (10.0, 48.0)
ESC_UP_XY = (90.0, 48.0)
ESC_DOWN_XY = (70.0, 48.0)


def _walk_seconds(distance_m: float) -> float:
    return round(max(distance_m, 0.01) / WALK_MPS, 2)


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return round(math.hypot(a[0] - b[0], a[1] - b[1]), 2)


def _hallway_key(floor_key: str, x: float, y: float) -> str:
    return f"h-{floor_key}-{int(x)}-{int(y)}"


def _nearest_grid(x: float, y: float) -> tuple[float, float]:
    return min(((gx, gy) for gx in XS for gy in YS), key=lambda p: _dist((x, y), p))


class _Builder:
    def __init__(self) -> None:
        self.nodes: dict[str, SeedNode] = {}
        self.edges: list[SeedEdge] = []
        self.locations: list[SeedLocation] = []
        self._edge_keys: set[tuple[str, str]] = set()

    def add_node(
        self,
        key: str,
        floor_key: str,
        node_type: NodeType,
        x: float,
        y: float,
        location_slug: str | None = None,
    ) -> SeedNode:
        if key in self.nodes:
            raise RuntimeError(f"duplicate node key in builder: {key}")
        node = SeedNode(
            key=key,
            floor_key=floor_key,
            node_type=node_type,
            x=x,
            y=y,
            location_slug=location_slug,
        )
        self.nodes[key] = node
        return node

    def add_edge(
        self,
        from_key: str,
        to_key: str,
        *,
        distance_m: float,
        edge_type: EdgeType,
        accessible: bool,
        avg_seconds: float | None = None,
    ) -> None:
        pair = (from_key, to_key)
        if pair in self._edge_keys:
            raise RuntimeError(f"duplicate directed edge in builder: {from_key}->{to_key}")
        self._edge_keys.add(pair)
        seconds = avg_seconds if avg_seconds is not None else _walk_seconds(distance_m)
        self.edges.append(
            SeedEdge(
                from_node_key=from_key,
                to_node_key=to_key,
                distance_m=distance_m,
                edge_type=edge_type,
                accessible=accessible,
                avg_seconds=seconds,
            )
        )

    def bidir(
        self,
        a: str,
        b: str,
        *,
        distance_m: float,
        edge_type: EdgeType = EdgeType.HALLWAY,
        accessible: bool = True,
        avg_seconds: float | None = None,
    ) -> None:
        self.add_edge(
            a,
            b,
            distance_m=distance_m,
            edge_type=edge_type,
            accessible=accessible,
            avg_seconds=avg_seconds,
        )
        self.add_edge(
            b,
            a,
            distance_m=distance_m,
            edge_type=edge_type,
            accessible=accessible,
            avg_seconds=avg_seconds,
        )

    def attach_to_nearest_hallway(self, node_key: str, *, accessible: bool = True) -> None:
        node = self.nodes[node_key]
        gx, gy = _nearest_grid(node.x, node.y)
        hall_key = _hallway_key(node.floor_key, gx, gy)
        distance = _dist((node.x, node.y), (gx, gy))
        if distance <= 0:
            raise RuntimeError(f"{node_key} sits on a hallway junction; offset it")
        self.bidir(node_key, hall_key, distance_m=distance, accessible=accessible)

    def add_location(
        self,
        *,
        slug: str,
        name: str,
        category_slug: str,
        floor_key: str,
        node_type: NodeType,
        x: float,
        y: float,
        description: str | None = None,
        wheelchair_accessible: bool = True,
        existing_node_key: str | None = None,
    ) -> None:
        if existing_node_key is not None:
            node_key = existing_node_key
            node = self.nodes[node_key]
            if node.floor_key != floor_key:
                raise RuntimeError(f"location {slug} floor mismatch vs node {node_key}")
            node.location_slug = slug
        else:
            node_key = f"loc-{slug}"
            self.add_node(node_key, floor_key, node_type, x, y, location_slug=slug)
            self.attach_to_nearest_hallway(node_key, accessible=wheelchair_accessible)
        self.locations.append(
            SeedLocation(
                slug=slug,
                name=name,
                category_slug=category_slug,
                floor_key=floor_key,
                anchor_node_key=node_key,
                description=description,
                wheelchair_accessible=wheelchair_accessible,
            )
        )


def _build_hallway_grid(b: _Builder) -> None:
    for floor_key in FLOOR_KEYS:
        for x in XS:
            for y in YS:
                b.add_node(
                    _hallway_key(floor_key, x, y),
                    floor_key,
                    NodeType.HALLWAY_JUNCTION,
                    float(x),
                    float(y),
                )
        for y in YS:
            for x1, x2 in pairwise(XS):
                a = _hallway_key(floor_key, x1, y)
                c = _hallway_key(floor_key, x2, y)
                b.bidir(a, c, distance_m=float(x2 - x1))
        for x in XS:
            for y1, y2 in pairwise(YS):
                a = _hallway_key(floor_key, x, y1)
                c = _hallway_key(floor_key, x, y2)
                b.bidir(a, c, distance_m=float(y2 - y1))


def _build_vertical_shafts(b: _Builder) -> None:
    for floor_key in FLOOR_KEYS:
        b.add_node(f"elev-{floor_key}", floor_key, NodeType.ELEVATOR_LANDING, *ELEVATOR_XY)
        b.add_node(f"stairs-{floor_key}", floor_key, NodeType.STAIRS_LANDING, *STAIRS_XY)
        b.add_node(f"esc-up-{floor_key}", floor_key, NodeType.ESCALATOR_UP_LANDING, *ESC_UP_XY)
        b.add_node(
            f"esc-down-{floor_key}", floor_key, NodeType.ESCALATOR_DOWN_LANDING, *ESC_DOWN_XY
        )
        for key in (
            f"elev-{floor_key}",
            f"stairs-{floor_key}",
            f"esc-up-{floor_key}",
            f"esc-down-{floor_key}",
        ):
            # Stairs/escalator spurs remain walkable; the *vertical* edges
            # carry accessible=false. A wheelchair user can reach the landing
            # and then must take the elevator.
            b.attach_to_nearest_hallway(key, accessible=True)

    adjacent = (
        (FLOOR_GROUND, FLOOR_L1),
        (FLOOR_L1, FLOOR_L2),
    )
    for lower, upper in adjacent:
        b.bidir(
            f"elev-{lower}",
            f"elev-{upper}",
            distance_m=0.0,
            edge_type=EdgeType.ELEVATOR,
            accessible=True,
            avg_seconds=25.0,
        )
        b.bidir(
            f"stairs-{lower}",
            f"stairs-{upper}",
            distance_m=12.0,
            edge_type=EdgeType.STAIRS,
            accessible=False,
            avg_seconds=40.0,
        )
        b.add_edge(
            f"esc-up-{lower}",
            f"esc-up-{upper}",
            distance_m=8.0,
            edge_type=EdgeType.ESCALATOR_UP,
            accessible=False,
            avg_seconds=20.0,
        )
        b.add_edge(
            f"esc-down-{upper}",
            f"esc-down-{lower}",
            distance_m=8.0,
            edge_type=EdgeType.ESCALATOR_DOWN,
            accessible=False,
            avg_seconds=18.0,
        )


def _build_locations(b: _Builder) -> None:
    # --- Ground -----------------------------------------------------------
    b.add_location(
        slug="nike",
        name="Nike",
        category_slug="fashion",
        floor_key=FLOOR_GROUND,
        node_type=NodeType.STORE_ANCHOR,
        x=30.0,
        y=82.0,
        description="Sportswear flagship on the ground-floor north mall.",
    )
    b.add_location(
        slug="zara",
        name="Zara",
        category_slug="fashion",
        floor_key=FLOOR_GROUND,
        node_type=NodeType.STORE_ANCHOR,
        x=50.0,
        y=82.0,
        description="Fast-fashion retailer facing the north corridor.",
    )
    b.add_location(
        slug="hm",
        name="H&M",
        category_slug="fashion",
        floor_key=FLOOR_GROUND,
        node_type=NodeType.STORE_ANCHOR,
        x=70.0,
        y=82.0,
        description="Apparel and home basics.",
    )
    b.add_location(
        slug="starbucks",
        name="Starbucks",
        category_slug="food",
        floor_key=FLOOR_GROUND,
        node_type=NodeType.STORE_ANCHOR,
        x=30.0,
        y=0.0,
        description="Coffee near the main entrance corridor.",
    )
    b.add_location(
        slug="mcdonalds",
        name="McDonald's",
        category_slug="food",
        floor_key=FLOOR_GROUND,
        node_type=NodeType.STORE_ANCHOR,
        x=70.0,
        y=0.0,
        description="Quick-service restaurant on the south mall.",
    )
    b.add_location(
        slug="super-pharm",
        name="Super-Pharm",
        category_slug="services",
        floor_key=FLOOR_GROUND,
        node_type=NodeType.STORE_ANCHOR,
        x=90.0,
        y=82.0,
        description="Pharmacy and personal care.",
    )
    b.add_location(
        slug="guest-services",
        name="Guest Services",
        category_slug="services",
        floor_key=FLOOR_GROUND,
        node_type=NodeType.INFO_DESK,
        x=110.0,
        y=82.0,
        description="Information desk, lost-and-found, and mall map handouts.",
    )
    b.add_location(
        slug="main-entrance",
        name="Main Entrance",
        category_slug="entrance",
        floor_key=FLOOR_GROUND,
        node_type=NodeType.ENTRANCE,
        x=50.0,
        y=0.0,
        description="Primary street entrance on the south facade.",
    )
    b.add_location(
        slug="parking-entrance",
        name="Parking Entrance",
        category_slug="entrance",
        floor_key=FLOOR_GROUND,
        node_type=NodeType.ENTRANCE,
        x=0.0,
        y=10.0,
        description="Entrance from the west parking garage.",
    )
    b.add_location(
        slug="restroom-g-north",
        name="Restroom — Ground North",
        category_slug="restroom",
        floor_key=FLOOR_GROUND,
        node_type=NodeType.BATHROOM,
        x=10.0,
        y=82.0,
        description="Public restrooms on the north corridor.",
    )
    b.add_location(
        slug="restroom-g-south",
        name="Restroom — Ground South",
        category_slug="restroom",
        floor_key=FLOOR_GROUND,
        node_type=NodeType.BATHROOM,
        x=110.0,
        y=0.0,
        description="Public restrooms near the east end of the south mall.",
    )
    b.add_location(
        slug="atm-g",
        name="ATM — Ground",
        category_slug="atm",
        floor_key=FLOOR_GROUND,
        node_type=NodeType.ATM,
        x=48.0,
        y=32.0,
        description="Bank ATM next to the central elevator lobby.",
    )
    b.add_location(
        slug="elevator-g",
        name="Elevator — Ground",
        category_slug="elevator",
        floor_key=FLOOR_GROUND,
        node_type=NodeType.ELEVATOR_LANDING,
        x=ELEVATOR_XY[0],
        y=ELEVATOR_XY[1],
        description="Central passenger elevator lobby on the ground floor.",
        existing_node_key="elev-ground",
    )
    b.add_location(
        slug="escalator-up-g",
        name="Escalator up — Ground to Level 1",
        category_slug="escalator",
        floor_key=FLOOR_GROUND,
        node_type=NodeType.ESCALATOR_UP_LANDING,
        x=ESC_UP_XY[0],
        y=ESC_UP_XY[1],
        description="Up-only escalator from Ground to Level 1.",
        wheelchair_accessible=False,
        existing_node_key="esc-up-ground",
    )
    b.add_location(
        slug="stairs-west-g",
        name="West Stairs — Ground",
        category_slug="stairs",
        floor_key=FLOOR_GROUND,
        node_type=NodeType.STAIRS_LANDING,
        x=STAIRS_XY[0],
        y=STAIRS_XY[1],
        description="West fire-stair landing. Not wheelchair accessible.",
        wheelchair_accessible=False,
        existing_node_key="stairs-ground",
    )

    # --- Level 1 ----------------------------------------------------------
    b.add_location(
        slug="apple",
        name="Apple",
        category_slug="electronics",
        floor_key=FLOOR_L1,
        node_type=NodeType.STORE_ANCHOR,
        x=30.0,
        y=82.0,
        description="Electronics store on Level 1 north.",
    )
    b.add_location(
        slug="samsung",
        name="Samsung",
        category_slug="electronics",
        floor_key=FLOOR_L1,
        node_type=NodeType.STORE_ANCHOR,
        x=70.0,
        y=82.0,
        description="Mobile and home electronics.",
    )
    b.add_location(
        slug="adidas",
        name="Adidas",
        category_slug="fashion",
        floor_key=FLOOR_L1,
        node_type=NodeType.STORE_ANCHOR,
        x=90.0,
        y=82.0,
        description="Sportswear on the north mall.",
    )
    b.add_location(
        slug="pizza-napoli",
        name="Pizza Napoli",
        category_slug="food",
        floor_key=FLOOR_L1,
        node_type=NodeType.STORE_ANCHOR,
        x=30.0,
        y=0.0,
        description="Food-court pizzeria.",
    )
    b.add_location(
        slug="sushi-kaito",
        name="Sushi Kaito",
        category_slug="food",
        floor_key=FLOOR_L1,
        node_type=NodeType.STORE_ANCHOR,
        x=50.0,
        y=0.0,
        description="Food-court sushi counter.",
    )
    b.add_location(
        slug="nova-cinema",
        name="NOVA Cinema",
        category_slug="services",
        floor_key=FLOOR_L1,
        node_type=NodeType.STORE_ANCHOR,
        x=110.0,
        y=82.0,
        description="Multiplex cinema at the east end of Level 1.",
    )
    b.add_location(
        slug="restroom-l1",
        name="Restroom — Level 1",
        category_slug="restroom",
        floor_key=FLOOR_L1,
        node_type=NodeType.BATHROOM,
        x=10.0,
        y=82.0,
        description="Public restrooms on Level 1 north.",
    )
    b.add_location(
        slug="atm-l1",
        name="ATM — Level 1",
        category_slug="atm",
        floor_key=FLOOR_L1,
        node_type=NodeType.ATM,
        x=48.0,
        y=32.0,
        description="ATM beside the Level 1 elevator lobby.",
    )
    b.add_location(
        slug="elevator-l1",
        name="Elevator — Level 1",
        category_slug="elevator",
        floor_key=FLOOR_L1,
        node_type=NodeType.ELEVATOR_LANDING,
        x=ELEVATOR_XY[0],
        y=ELEVATOR_XY[1],
        description="Central passenger elevator lobby on Level 1.",
        existing_node_key="elev-l1",
    )
    b.add_location(
        slug="escalator-up-l1",
        name="Escalator up — Level 1 to Level 2",
        category_slug="escalator",
        floor_key=FLOOR_L1,
        node_type=NodeType.ESCALATOR_UP_LANDING,
        x=ESC_UP_XY[0],
        y=ESC_UP_XY[1],
        description="Up-only escalator from Level 1 to Level 2.",
        wheelchair_accessible=False,
        existing_node_key="esc-up-l1",
    )

    # --- Level 2 ----------------------------------------------------------
    b.add_location(
        slug="muji",
        name="MUJI",
        category_slug="fashion",
        floor_key=FLOOR_L2,
        node_type=NodeType.STORE_ANCHOR,
        x=30.0,
        y=82.0,
        description="Home goods and apparel.",
    )
    b.add_location(
        slug="pages-bookstore",
        name="Pages Bookstore",
        category_slug="services",
        floor_key=FLOOR_L2,
        node_type=NodeType.STORE_ANCHOR,
        x=70.0,
        y=82.0,
        description="Books, stationery, and a small cafe corner.",
    )
    b.add_location(
        slug="rooftop-cafe",
        name="Rooftop Cafe",
        category_slug="food",
        floor_key=FLOOR_L2,
        node_type=NodeType.STORE_ANCHOR,
        x=50.0,
        y=0.0,
        description="Cafe with terrace seating on Level 2 south.",
    )
    b.add_location(
        slug="restroom-l2",
        name="Restroom — Level 2",
        category_slug="restroom",
        floor_key=FLOOR_L2,
        node_type=NodeType.BATHROOM,
        x=10.0,
        y=82.0,
        description="Public restrooms on Level 2 north.",
    )
    b.add_location(
        slug="atm-l2",
        name="ATM — Level 2",
        category_slug="atm",
        floor_key=FLOOR_L2,
        node_type=NodeType.ATM,
        x=48.0,
        y=32.0,
        description="ATM beside the Level 2 elevator lobby.",
    )
    b.add_location(
        slug="elevator-l2",
        name="Elevator — Level 2",
        category_slug="elevator",
        floor_key=FLOOR_L2,
        node_type=NodeType.ELEVATOR_LANDING,
        x=ELEVATOR_XY[0],
        y=ELEVATOR_XY[1],
        description="Central passenger elevator lobby on Level 2.",
        existing_node_key="elev-l2",
    )


def _categories() -> list[SeedCategory]:
    return [
        SeedCategory(slug="fashion", name_en="Fashion", name_he="אופנה", name_ar="أزياء"),
        SeedCategory(
            slug="electronics", name_en="Electronics", name_he="אלקטרוניקה", name_ar="إلكترونيات"
        ),
        SeedCategory(slug="food", name_en="Food", name_he="אוכל", name_ar="طعام"),
        SeedCategory(slug="services", name_en="Services", name_he="שירותים", name_ar="خدمات"),
        SeedCategory(
            slug="restroom", name_en="Restroom", name_he="שירותי נוחיות", name_ar="دورة مياه"
        ),
        SeedCategory(slug="atm", name_en="ATM", name_he="כספומט", name_ar="صراف آلي"),
        SeedCategory(slug="elevator", name_en="Elevator", name_he="מעלית", name_ar="مصعد"),
        SeedCategory(slug="escalator", name_en="Escalator", name_he="דרגנוע", name_ar="سلم متحرك"),
        SeedCategory(slug="entrance", name_en="Entrance", name_he="כניסה", name_ar="مدخل"),
        SeedCategory(slug="stairs", name_en="Stairs", name_he="מדרגות", name_ar="سلالم"),
    ]


def build_nova_mall() -> SeedDocument:
    """Return a fully-populated, not-yet-validated seed document."""
    b = _Builder()
    _build_hallway_grid(b)
    _build_vertical_shafts(b)
    _build_locations(b)
    return SeedDocument(
        mall=SeedMall(slug="nova-mall", name="NOVA Mall", city="Fictional City", timezone="UTC"),
        floors=[
            SeedFloor(key=FLOOR_GROUND, level=0, name="Ground Floor", display_order=0),
            SeedFloor(key=FLOOR_L1, level=1, name="Level 1", display_order=1),
            SeedFloor(key=FLOOR_L2, level=2, name="Level 2", display_order=2),
        ],
        categories=_categories(),
        locations=b.locations,
        nodes=list(b.nodes.values()),
        edges=b.edges,
    )


def iter_fatal_issues(doc: SeedDocument | None = None) -> Iterable[str]:
    """Helper for `python -m app.seed --validate-only`."""
    from app.seed.validator import validate_seed

    for issue in validate_seed(doc or build_nova_mall()):
        if issue.fatal:
            yield f"[{issue.kind}] {issue.where}: {issue.message}"
