"""Edge-allow predicates for route profiles.

Algorithms never mention stairs vs elevators. They expand `outgoing` edges
that this policy accepts. That keeps Dijkstra/A* identical across profiles
and puts accessibility rules in one place that tests can target.
"""

from __future__ import annotations

from collections.abc import Callable

from app.models.enums import EdgeType
from app.routing.types import CostMode, GraphEdge, RouteProfile

EdgeFilter = Callable[[GraphEdge], bool]


def edge_cost(edge: GraphEdge, mode: CostMode) -> float:
    if mode is CostMode.DISTANCE:
        return edge.distance_m
    return edge.avg_seconds


def allow_all(_edge: GraphEdge) -> bool:
    return True


def allow_wheelchair(edge: GraphEdge) -> bool:
    return edge.accessible


def allow_avoid_stairs(edge: GraphEdge) -> bool:
    return edge.edge_type is not EdgeType.STAIRS


def filter_for(profile: RouteProfile) -> EdgeFilter:
    if profile is RouteProfile.WHEELCHAIR:
        return allow_wheelchair
    if profile is RouteProfile.AVOID_STAIRS:
        return allow_avoid_stairs
    return allow_all
