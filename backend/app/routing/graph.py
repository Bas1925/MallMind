"""Build an in-memory MallGraph from a seed document or ORM rows."""

from __future__ import annotations

import uuid

from app.models.enums import EdgeType, NodeType
from app.routing.types import GraphEdge, GraphNode, MallGraph
from app.schemas.seed import SeedDocument

_SEED_NS = uuid.UUID("8f3c1e2a-6b90-4d11-9c4e-1a2b3c4d5e6f")


def seed_location_id(slug: str) -> uuid.UUID:
    return uuid.uuid5(_SEED_NS, f"loc:{slug}")


def seed_node_id(key: str) -> uuid.UUID:
    return uuid.uuid5(_SEED_NS, f"node:{key}")


def seed_edge_id(from_key: str, to_key: str) -> uuid.UUID:
    return uuid.uuid5(_SEED_NS, f"edge:{from_key}->{to_key}")


def graph_from_seed(doc: SeedDocument) -> MallGraph:
    floor_level = {f.key: f.level for f in doc.floors}
    floor_ids = {f.key: uuid.uuid5(_SEED_NS, f"floor:{f.key}") for f in doc.floors}
    loc_ids = {loc.slug: seed_location_id(loc.slug) for loc in doc.locations}
    anchor_slug = {loc.anchor_node_key: loc.slug for loc in doc.locations}

    nodes: dict[uuid.UUID, GraphNode] = {}
    by_key: dict[str, uuid.UUID] = {}
    by_location_id: dict[uuid.UUID, uuid.UUID] = {}
    for n in doc.nodes:
        nid = seed_node_id(n.key)
        loc_id = loc_ids.get(n.location_slug) if n.location_slug else None
        if n.key in anchor_slug:
            loc_id = loc_ids[anchor_slug[n.key]]
        node = GraphNode(
            id=nid,
            floor_id=floor_ids[n.floor_key],
            floor_level=floor_level[n.floor_key],
            x=n.x,
            y=n.y,
            node_type=n.node_type if isinstance(n.node_type, NodeType) else NodeType(n.node_type),
            location_id=loc_id,
            key=n.key,
        )
        nodes[nid] = node
        by_key[n.key] = nid
        if loc_id is not None:
            by_location_id[loc_id] = nid

    outgoing: dict[uuid.UUID, list[GraphEdge]] = {nid: [] for nid in nodes}
    for e in doc.edges:
        edge = GraphEdge(
            id=seed_edge_id(e.from_node_key, e.to_node_key),
            from_id=by_key[e.from_node_key],
            to_id=by_key[e.to_node_key],
            distance_m=e.distance_m,
            avg_seconds=e.avg_seconds,
            accessible=e.accessible,
            edge_type=e.edge_type if isinstance(e.edge_type, EdgeType) else EdgeType(e.edge_type),
        )
        outgoing[edge.from_id].append(edge)
    return MallGraph(
        nodes=nodes,
        outgoing=outgoing,
        by_key=by_key,
        by_location_id=by_location_id,
        floor_names={f.level: f.name for f in doc.floors},
    )
