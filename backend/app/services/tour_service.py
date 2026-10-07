"""Build a pairwise A* matrix and choose an open visit order.

The matrix is the cache for this request. Pairs are not recomputed when the
order is stitched back into graph routes.
"""

from __future__ import annotations

import logging
import math
import time
import uuid
from dataclasses import dataclass
from itertools import pairwise

from app.models import Location
from app.repositories.graph_repository import GraphRepository
from app.routing.astar import astar
from app.routing.instructions import floors_on_route, instructions_for
from app.routing.policy import filter_for
from app.routing.tour import EPS, EXACT_MAX_STOPS, path_cost, solve_tour, unreachable_from_start
from app.routing.types import CostMode, MallGraph, RouteProfile, RouteResult
from app.services.navigation import NavigationError

logger = logging.getLogger(__name__)

# 20 stops is the product cap. Held-Karp above EXACT_MAX_STOPS is the
# algorithm cap; bench_tour.py is what justifies both numbers.
MAX_STOPS = 20


@dataclass(frozen=True)
class PlannedStop:
    location_id: uuid.UUID
    name: str
    slug: str
    floor: str
    floor_level: int


@dataclass(frozen=True)
class PlannedSegment:
    from_location_id: uuid.UUID
    to_location_id: uuid.UUID
    distance_m: float
    estimated_seconds: float
    floors: list[int]
    node_ids: list[uuid.UUID]
    instructions: list[str]


@dataclass(frozen=True)
class TourPlan:
    original_order: list[PlannedStop]
    optimized_order: list[PlannedStop]
    original_distance_m: float
    optimized_distance_m: float
    distance_saved_m: float
    distance_saved_percent: float | None
    original_seconds: float
    optimized_seconds: float
    estimated_time_saved_seconds: float
    floor_changes_original: int
    floor_changes_optimized: int
    algorithm: str
    improved: bool
    message: str | None
    segments: list[PlannedSegment]
    node_ids: list[uuid.UUID]
    instructions: list[str]
    floors: list[int]
    profile: str
    cost_mode: str
    astar_calls: int
    two_opt_moves: int
    nearest_neighbor_distance_m: float
    nearest_neighbor_2opt_distance_m: float
    exact_distance_m: float | None
    nearest_neighbor_gap_percent: float | None
    nearest_neighbor_2opt_gap_percent: float | None
    matrix_m: list[list[float | None]]
    labels: list[str]


class TourService:
    def __init__(self, repo: GraphRepository) -> None:
        self._repo = repo

    async def plan(
        self,
        start_location_id: uuid.UUID,
        stop_ids: list[uuid.UUID],
        *,
        profile: RouteProfile,
        cost_mode: CostMode,
    ) -> TourPlan:
        started = time.perf_counter()
        if len(stop_ids) == 0:
            raise NavigationError("empty_stops", "choose at least one stop")
        if len(stop_ids) > MAX_STOPS:
            raise NavigationError("too_many_stops", f"at most {MAX_STOPS} stops")
        if len(stop_ids) != len(set(stop_ids)) or start_location_id in stop_ids:
            raise NavigationError("duplicate_stop", "stops must be unique and not the start")

        graph = await self._repo.load_mall_graph()
        locations = [await self._load(start_location_id, "start_location_id")]
        for stop_id in stop_ids:
            locations.append(await self._load(stop_id, "location_id"))
        anchors = [_anchor(graph, loc) for loc in locations]

        distance, seconds, routes, calls = _pairs(graph, anchors, profile, cost_mode)
        objective = distance if cost_mode is CostMode.DISTANCE else seconds
        missing = unreachable_from_start(objective)
        if missing:
            names = ", ".join(locations[index].name for index in missing)
            if profile is RouteProfile.WHEELCHAIR:
                text = f"No wheelchair-accessible route exists to {names}."
            else:
                text = f"No route exists to {names} under profile {profile.value}."
            raise NavigationError(
                "unreachable_stop",
                text,
                location_ids=[str(locations[index].id) for index in missing],
            )

        solved = solve_tour(objective, exact=len(stop_ids) <= EXACT_MAX_STOPS)
        if solved is None:
            raise NavigationError(
                "no_tour",
                f"No single route visits every selected stop under profile {profile.value}.",
            )

        user_index = list(range(len(locations)))
        original_distance = path_cost(distance, user_index)
        optimized_distance = path_cost(distance, solved.order)
        original_seconds = path_cost(seconds, user_index)
        optimized_seconds = path_cost(seconds, solved.order)
        objective_saved = path_cost(objective, user_index) - path_cost(objective, solved.order)
        improved = objective_saved > EPS
        distance_saved = max(0.0, original_distance - optimized_distance)
        time_saved = max(0.0, original_seconds - optimized_seconds)

        segments = _segments(locations, routes, solved.order, graph)
        node_ids = _stitch(segments)
        opt_stops = [_stop(locations[index]) for index in solved.order]
        user_stops = [_stop(locations[index]) for index in user_index]
        nn_distance = _finite_distance(distance, solved.nn_order)
        polished_distance = _finite_distance(distance, solved.nn_2opt_order)
        exact_distance = (
            _finite_distance(distance, solved.exact_order) if solved.exact_order else None
        )

        plan = TourPlan(
            original_order=user_stops,
            optimized_order=opt_stops,
            original_distance_m=_round_m(original_distance),
            optimized_distance_m=_round_m(optimized_distance),
            distance_saved_m=_round_m(distance_saved) if improved else 0.0,
            distance_saved_percent=_percent(original_distance, distance_saved) if improved else 0.0,
            original_seconds=round(original_seconds, 1),
            optimized_seconds=round(optimized_seconds, 1),
            estimated_time_saved_seconds=round(time_saved) if improved else 0,
            floor_changes_original=_floor_changes(graph, routes, user_index),
            floor_changes_optimized=_floor_changes(graph, routes, solved.order),
            algorithm=solved.algorithm,
            improved=improved,
            message=None if improved else _unchanged_message(cost_mode),
            segments=segments,
            node_ids=node_ids,
            instructions=[line for segment in segments for line in segment.instructions],
            floors=_floors(graph, node_ids),
            profile=profile.value,
            cost_mode=cost_mode.value,
            astar_calls=calls,
            two_opt_moves=solved.two_opt_moves,
            nearest_neighbor_distance_m=_round_m(nn_distance) if nn_distance is not None else 0.0,
            nearest_neighbor_2opt_distance_m=(
                _round_m(polished_distance) if polished_distance is not None else 0.0
            ),
            exact_distance_m=_round_m(exact_distance) if exact_distance is not None else None,
            nearest_neighbor_gap_percent=_gap(nn_distance, exact_distance),
            nearest_neighbor_2opt_gap_percent=_gap(polished_distance, exact_distance),
            matrix_m=[
                [None if math.isinf(value) else _round_m(value) for value in row]
                for row in distance
            ],
            labels=[loc.name for loc in locations],
        )
        logger.info(
            "tour stops=%s profile=%s algorithm=%s astar=%s improved=%s ms=%s",
            len(stop_ids),
            profile.value,
            solved.algorithm,
            calls,
            improved,
            int((time.perf_counter() - started) * 1000),
        )
        return plan

    async def _load(self, location_id: uuid.UUID, field: str) -> Location:
        loc = await self._repo.get_location(location_id)
        if loc is None:
            raise NavigationError("unknown_location", f"{field} was not found")
        return loc


def _anchor(graph: MallGraph, loc: Location) -> uuid.UUID:
    if loc.anchor_node is None:
        raise NavigationError("missing_anchor", f"{loc.slug} has no map anchor")
    if loc.anchor_node.id not in graph.nodes:
        raise NavigationError("unknown_node", "location anchor is missing from the graph")
    return loc.anchor_node.id


def _pairs(
    graph: MallGraph,
    anchors: list[uuid.UUID],
    profile: RouteProfile,
    cost_mode: CostMode,
) -> tuple[list[list[float]], list[list[float]], dict[tuple[int, int], RouteResult], int]:
    n = len(anchors)
    distance = [[0.0] * n for _ in range(n)]
    seconds = [[0.0] * n for _ in range(n)]
    routes: dict[tuple[int, int], RouteResult] = {}
    allow = filter_for(profile)
    calls = 0
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            calls += 1
            result = astar(
                graph,
                anchors[i],
                anchors[j],
                cost_mode=cost_mode,
                allow=allow,
            )
            routes[(i, j)] = result
            if result.ok:
                distance[i][j] = result.total_distance_m
                seconds[i][j] = result.total_seconds
            else:
                distance[i][j] = math.inf
                seconds[i][j] = math.inf
    return distance, seconds, routes, calls


def _segments(
    locations: list[Location],
    routes: dict[tuple[int, int], RouteResult],
    order: list[int],
    graph: MallGraph,
) -> list[PlannedSegment]:
    segments: list[PlannedSegment] = []
    for left, right in pairwise(order):
        result = routes[(left, right)]
        dest = locations[right]
        segments.append(
            PlannedSegment(
                from_location_id=locations[left].id,
                to_location_id=dest.id,
                distance_m=result.total_distance_m,
                estimated_seconds=result.total_seconds,
                floors=floors_on_route(graph, result.node_ids),
                node_ids=list(result.node_ids),
                instructions=instructions_for(graph, result, destination_name=dest.name),
            )
        )
    return segments


def _stitch(segments: list[PlannedSegment]) -> list[uuid.UUID]:
    combined: list[uuid.UUID] = []
    for segment in segments:
        ids = segment.node_ids
        if combined and ids and combined[-1] == ids[0]:
            combined.extend(ids[1:])
        else:
            combined.extend(ids)
    return combined


def _floors(graph: MallGraph, node_ids: list[uuid.UUID]) -> list[int]:
    levels: list[int] = []
    for node_id in node_ids:
        node = graph.nodes.get(node_id)
        if node is None:
            continue
        if not levels or levels[-1] != node.floor_level:
            levels.append(node.floor_level)
    return levels


def _floor_changes(
    graph: MallGraph,
    routes: dict[tuple[int, int], RouteResult],
    order: list[int],
) -> int:
    changes = 0
    for left, right in pairwise(order):
        result = routes.get((left, right))
        if result is None or not result.ok:
            continue
        previous: int | None = None
        for node_id in result.node_ids:
            level = graph.nodes[node_id].floor_level
            if previous is not None and level != previous:
                changes += 1
            previous = level
    return changes


def _stop(loc: Location) -> PlannedStop:
    return PlannedStop(
        location_id=loc.id,
        name=loc.name,
        slug=loc.slug,
        floor=loc.floor.name,
        floor_level=loc.floor.level,
    )


def _finite_distance(distance: list[list[float]], order: list[int]) -> float | None:
    if len(order) != len(distance):
        return None
    total = path_cost(distance, order)
    if math.isinf(total):
        return None
    return total


def _round_m(value: float) -> float:
    return round(value, 1)


def _percent(original: float, saved: float) -> float | None:
    if original <= EPS:
        return None
    return round(100.0 * saved / original, 1)


def _gap(heuristic: float | None, exact: float | None) -> float | None:
    if heuristic is None or exact is None or exact <= EPS:
        return None
    return round(100.0 * (heuristic - exact) / exact, 1)


def _unchanged_message(cost_mode: CostMode) -> str:
    if cost_mode is CostMode.TIME:
        return "No faster route was found."
    return "No shorter route was found."
