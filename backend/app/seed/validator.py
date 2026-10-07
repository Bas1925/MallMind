"""Cross-reference and topology validation for a mall seed.

Runs against the parsed `SeedDocument`, *before* any database writes.
Collects every problem and returns them together — a single run should
show an author every issue, not just the first one.

This module never mutates the seed. Invalid data is refused, not repaired.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass

from app.models.enums import VERTICAL_EDGE_TYPES, EdgeType, NodeType
from app.schemas.seed import SeedDocument


@dataclass(frozen=True)
class SeedIssue:
    kind: str
    message: str
    where: str
    fatal: bool = True


class SeedValidationError(Exception):
    """Raised when the seed contains one or more fatal issues."""

    def __init__(self, issues: list[SeedIssue]) -> None:
        self.issues = issues
        fatal = [i for i in issues if i.fatal]
        preview = "; ".join(f"[{i.kind}] {i.message}" for i in fatal[:8])
        extra = f" (+{len(fatal) - 8} more)" if len(fatal) > 8 else ""
        super().__init__(f"{len(fatal)} seed validation error(s): {preview}{extra}")


# Node types that are allowed as a location's sole anchor.
_ANCHOR_TYPES_BY_CATEGORY: dict[str, frozenset[NodeType]] = {
    "fashion": frozenset({NodeType.STORE_ANCHOR}),
    "electronics": frozenset({NodeType.STORE_ANCHOR}),
    "food": frozenset({NodeType.STORE_ANCHOR}),
    "services": frozenset({NodeType.STORE_ANCHOR, NodeType.INFO_DESK}),
    "restroom": frozenset({NodeType.BATHROOM}),
    "atm": frozenset({NodeType.ATM}),
    "entrance": frozenset({NodeType.ENTRANCE, NodeType.EXIT}),
    "elevator": frozenset({NodeType.ELEVATOR_LANDING}),
    "escalator": frozenset({NodeType.ESCALATOR_UP_LANDING, NodeType.ESCALATOR_DOWN_LANDING}),
    "stairs": frozenset({NodeType.STAIRS_LANDING}),
}

# Vertical edges may only join matching landing types.
_EDGE_TYPE_TO_LANDING: dict[EdgeType, NodeType] = {
    EdgeType.ELEVATOR: NodeType.ELEVATOR_LANDING,
    EdgeType.STAIRS: NodeType.STAIRS_LANDING,
    EdgeType.ESCALATOR_UP: NodeType.ESCALATOR_UP_LANDING,
    EdgeType.ESCALATOR_DOWN: NodeType.ESCALATOR_DOWN_LANDING,
}


def validate_seed(doc: SeedDocument) -> list[SeedIssue]:
    """Return every issue found. Empty list means the seed is acceptable."""
    issues: list[SeedIssue] = []
    issues.extend(_check_uniqueness(doc))
    issues.extend(_check_references(doc))
    issues.extend(_check_numeric(doc))
    issues.extend(_check_topology(doc))
    issues.extend(_check_reachability(doc))
    issues.extend(_check_orphans(doc))
    return issues


def assert_valid(doc: SeedDocument) -> None:
    issues = validate_seed(doc)
    fatal = [i for i in issues if i.fatal]
    if fatal:
        raise SeedValidationError(issues)


def _check_uniqueness(doc: SeedDocument) -> list[SeedIssue]:
    issues: list[SeedIssue] = []

    def dupes(values: list[str], label: str, where: str) -> None:
        seen: set[str] = set()
        for v in values:
            if v in seen:
                issues.append(SeedIssue("duplicate", f"duplicate {label} {v!r}", where))
            seen.add(v)

    dupes([f.key for f in doc.floors], "floor key", "floors")
    dupes([str(f.level) for f in doc.floors], "floor level", "floors")
    dupes([c.slug for c in doc.categories], "category slug", "categories")
    dupes([loc.slug for loc in doc.locations], "location slug", "locations")
    dupes([n.key for n in doc.nodes], "node key", "nodes")
    dupes(
        [f"{e.from_node_key}->{e.to_node_key}" for e in doc.edges],
        "directed edge",
        "edges",
    )
    return issues


def _check_references(doc: SeedDocument) -> list[SeedIssue]:
    issues: list[SeedIssue] = []
    floor_keys = {f.key for f in doc.floors}
    category_slugs = {c.slug for c in doc.categories}
    node_keys = {n.key for n in doc.nodes}
    location_slugs = {loc.slug for loc in doc.locations}

    for n in doc.nodes:
        if n.floor_key not in floor_keys:
            issues.append(
                SeedIssue(
                    "missing_ref",
                    f"node {n.key!r} references unknown floor {n.floor_key!r}",
                    f"nodes.{n.key}",
                )
            )
        if n.location_slug is not None and n.location_slug not in location_slugs:
            issues.append(
                SeedIssue(
                    "missing_ref",
                    f"node {n.key!r} references unknown location {n.location_slug!r}",
                    f"nodes.{n.key}",
                )
            )

    for loc in doc.locations:
        if loc.floor_key not in floor_keys:
            issues.append(
                SeedIssue(
                    "missing_ref",
                    f"location {loc.slug!r} references unknown floor {loc.floor_key!r}",
                    f"locations.{loc.slug}",
                )
            )
        if loc.category_slug not in category_slugs:
            issues.append(
                SeedIssue(
                    "missing_ref",
                    f"location {loc.slug!r} references unknown category {loc.category_slug!r}",
                    f"locations.{loc.slug}",
                )
            )
        if loc.anchor_node_key not in node_keys:
            issues.append(
                SeedIssue(
                    "missing_ref",
                    f"location {loc.slug!r} references unknown anchor node {loc.anchor_node_key!r}",
                    f"locations.{loc.slug}",
                )
            )

    for i, e in enumerate(doc.edges):
        where = f"edges[{i}] {e.from_node_key}->{e.to_node_key}"
        if e.from_node_key not in node_keys:
            issues.append(
                SeedIssue(
                    "missing_ref",
                    f"edge from unknown node {e.from_node_key!r}",
                    where,
                )
            )
        if e.to_node_key not in node_keys:
            issues.append(
                SeedIssue(
                    "missing_ref",
                    f"edge to unknown node {e.to_node_key!r}",
                    where,
                )
            )
    return issues


def _check_numeric(doc: SeedDocument) -> list[SeedIssue]:
    issues: list[SeedIssue] = []
    for i, e in enumerate(doc.edges):
        where = f"edges[{i}] {e.from_node_key}->{e.to_node_key}"
        if e.from_node_key == e.to_node_key:
            issues.append(SeedIssue("self_loop", "self-loop edge is not allowed", where))
        if e.distance_m < 0:
            issues.append(
                SeedIssue("distance", f"distance_m must be >= 0, got {e.distance_m}", where)
            )
        if e.edge_type == EdgeType.HALLWAY and e.distance_m <= 0:
            issues.append(
                SeedIssue(
                    "distance",
                    "hallway edges must have distance_m > 0",
                    where,
                )
            )
        if e.avg_seconds <= 0:
            issues.append(SeedIssue("time", f"avg_seconds must be > 0, got {e.avg_seconds}", where))
    return issues


def _check_topology(doc: SeedDocument) -> list[SeedIssue]:
    issues: list[SeedIssue] = []
    floors_by_key = {f.key: f for f in doc.floors}
    nodes_by_key = {n.key: n for n in doc.nodes}

    # Each location has exactly one anchor; that node is on the same floor.
    anchors_used: dict[str, str] = {}
    for loc in doc.locations:
        node = nodes_by_key.get(loc.anchor_node_key)
        if node is None:
            continue
        if loc.anchor_node_key in anchors_used:
            issues.append(
                SeedIssue(
                    "anchor",
                    f"node {loc.anchor_node_key!r} is already the anchor for "
                    f"{anchors_used[loc.anchor_node_key]!r}",
                    f"locations.{loc.slug}",
                )
            )
        anchors_used[loc.anchor_node_key] = loc.slug
        if node.floor_key != loc.floor_key:
            issues.append(
                SeedIssue(
                    "anchor",
                    (
                        f"anchor node is on floor {node.floor_key!r} "
                        f"but location is on {loc.floor_key!r}"
                    ),
                    f"locations.{loc.slug}",
                )
            )
        allowed = _ANCHOR_TYPES_BY_CATEGORY.get(loc.category_slug)
        if allowed is not None and node.node_type not in allowed:
            issues.append(
                SeedIssue(
                    "anchor",
                    f"category {loc.category_slug!r} cannot be anchored on a "
                    f"{node.node_type.value} node",
                    f"locations.{loc.slug}",
                )
            )
        if node.location_slug is not None and node.location_slug != loc.slug:
            issues.append(
                SeedIssue(
                    "anchor",
                    f"anchor node {node.key!r} is labelled with location "
                    f"{node.location_slug!r} but is used by {loc.slug!r}",
                    f"locations.{loc.slug}",
                )
            )

    for i, e in enumerate(doc.edges):
        src = nodes_by_key.get(e.from_node_key)
        dst = nodes_by_key.get(e.to_node_key)
        if src is None or dst is None:
            continue
        where = f"edges[{i}] {e.from_node_key}->{e.to_node_key}"
        src_floor = floors_by_key.get(src.floor_key)
        dst_floor = floors_by_key.get(dst.floor_key)
        if src_floor is None or dst_floor is None:
            continue

        same_floor = src.floor_key == dst.floor_key
        if e.edge_type == EdgeType.HALLWAY:
            if not same_floor:
                issues.append(
                    SeedIssue(
                        "illegal_vertical",
                        "hallway edges must connect nodes on the same floor",
                        where,
                    )
                )
        elif e.edge_type in VERTICAL_EDGE_TYPES:
            if same_floor:
                issues.append(
                    SeedIssue(
                        "illegal_vertical",
                        f"{e.edge_type.value} edges must connect different floors",
                        where,
                    )
                )
            expected_landing = _EDGE_TYPE_TO_LANDING[e.edge_type]
            if src.node_type != expected_landing:
                issues.append(
                    SeedIssue(
                        "illegal_vertical",
                        f"{e.edge_type.value} from-node must be {expected_landing.value}, "
                        f"got {src.node_type.value}",
                        where,
                    )
                )
            if dst.node_type != expected_landing:
                issues.append(
                    SeedIssue(
                        "illegal_vertical",
                        f"{e.edge_type.value} to-node must be {expected_landing.value}, "
                        f"got {dst.node_type.value}",
                        where,
                    )
                )
            if abs(src.x - dst.x) > 0.01 or abs(src.y - dst.y) > 0.01:
                issues.append(
                    SeedIssue(
                        "illegal_vertical",
                        "vertical connectors must stack at the same (x, y)",
                        where,
                    )
                )
            if e.edge_type == EdgeType.ESCALATOR_UP and dst_floor.level <= src_floor.level:
                issues.append(
                    SeedIssue(
                        "illegal_vertical",
                        "escalator_up must go to a higher floor",
                        where,
                    )
                )
            if e.edge_type == EdgeType.ESCALATOR_DOWN and dst_floor.level >= src_floor.level:
                issues.append(
                    SeedIssue(
                        "illegal_vertical",
                        "escalator_down must go to a lower floor",
                        where,
                    )
                )
            adjacent = abs(dst_floor.level - src_floor.level) == 1
            if (
                e.edge_type in {EdgeType.STAIRS, EdgeType.ESCALATOR_UP, EdgeType.ESCALATOR_DOWN}
                and not adjacent
            ):
                issues.append(
                    SeedIssue(
                        "illegal_vertical",
                        f"{e.edge_type.value} must connect adjacent floors "
                        f"(got {src_floor.level} -> {dst_floor.level})",
                        where,
                    )
                )
    return issues


def _check_reachability(doc: SeedDocument) -> list[SeedIssue]:
    issues: list[SeedIssue] = []
    adj: dict[str, list[tuple[str, bool]]] = defaultdict(list)
    for e in doc.edges:
        adj[e.from_node_key].append((e.to_node_key, e.accessible))

    entrances = [n.key for n in doc.nodes if n.node_type == NodeType.ENTRANCE]
    if not entrances:
        issues.append(
            SeedIssue("reachability", "seed has no entrance node to start BFS from", "nodes")
        )
        return issues

    start = entrances[0]
    reachable_any = _bfs(adj, start, accessible_only=False)
    reachable_acc = _bfs(adj, start, accessible_only=True)

    nodes_by_key = {n.key: n for n in doc.nodes}
    for loc in doc.locations:
        node = nodes_by_key.get(loc.anchor_node_key)
        if node is None:
            continue
        if loc.anchor_node_key not in reachable_any:
            issues.append(
                SeedIssue(
                    "reachability",
                    f"location {loc.slug!r} (anchor {loc.anchor_node_key!r}) "
                    f"is unreachable from entrance {start!r}",
                    f"locations.{loc.slug}",
                )
            )
        elif loc.anchor_node_key not in reachable_acc:
            issues.append(
                SeedIssue(
                    "reachability",
                    f"location {loc.slug!r} is unreachable in accessible mode "
                    f"from entrance {start!r}",
                    f"locations.{loc.slug}",
                    fatal=False,
                )
            )
    return issues


def _bfs(adj: dict[str, list[tuple[str, bool]]], start: str, *, accessible_only: bool) -> set[str]:
    seen: set[str] = {start}
    q: deque[str] = deque([start])
    while q:
        cur = q.popleft()
        for nxt, accessible in adj.get(cur, []):
            if accessible_only and not accessible:
                continue
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return seen


def _check_orphans(doc: SeedDocument) -> list[SeedIssue]:
    issues: list[SeedIssue] = []
    degree: dict[str, int] = defaultdict(int)
    for e in doc.edges:
        degree[e.from_node_key] += 1
        degree[e.to_node_key] += 1
    for n in doc.nodes:
        if degree[n.key] == 0:
            issues.append(
                SeedIssue(
                    "orphan",
                    f"node {n.key!r} has no incoming or outgoing edges",
                    f"nodes.{n.key}",
                    fatal=False,
                )
            )
    return issues
