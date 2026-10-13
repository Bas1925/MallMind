"""Location-to-location routing. Algorithms never see Location rows."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Location
from app.repositories.graph_repository import GraphRepository
from app.routing.astar import astar
from app.routing.dijkstra import dijkstra
from app.routing.instructions import floors_on_route, instructions_for
from app.routing.policy import filter_for
from app.routing.search import bfs, dfs
from app.routing.types import CostMode, MallGraph, RouteProfile, RouteResult

_STATUS = {
    "unknown_location": 404,
    "missing_anchor": 422,
    "same_location": 400,
    "invalid_profile": 400,
    "invalid_cost_mode": 400,
    "invalid_algorithm": 400,
    "no_path": 422,
    "no_accessible_path": 422,
    "unknown_node": 422,
    "empty_stops": 400,
    "duplicate_stop": 400,
    "too_many_stops": 400,
    "unreachable_stop": 422,
    "no_tour": 422,
}


class NavigationError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int | None = None,
        *,
        location_ids: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code if status_code is not None else _STATUS.get(code, 400)
        self.location_ids = location_ids or []


@dataclass
class NavigationRoute:
    result: RouteResult
    instructions: list[str]
    floors: list[int]
    from_location: Location
    to_location: Location
    graph: MallGraph
    profile: RouteProfile
    cost_mode: CostMode


class NavigationService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = GraphRepository(session)

    async def route(
        self,
        from_location_id: uuid.UUID | str,
        to_location_id: uuid.UUID | str,
        *,
        profile: RouteProfile | str = RouteProfile.NORMAL,
        cost_mode: CostMode | str = CostMode.DISTANCE,
        algorithm: str = "astar",
    ) -> NavigationRoute:
        try:
            pol = profile if isinstance(profile, RouteProfile) else RouteProfile(profile)
        except ValueError as exc:
            raise NavigationError("invalid_profile", f"unknown profile {profile!r}") from exc
        try:
            mode = cost_mode if isinstance(cost_mode, CostMode) else CostMode(cost_mode)
        except ValueError as exc:
            raise NavigationError("invalid_cost_mode", f"unknown cost_mode {cost_mode!r}") from exc
        algo = algorithm.lower().strip()
        routers = {"astar": astar, "dijkstra": dijkstra, "bfs": bfs, "dfs": dfs}
        router = routers.get(algo)
        if router is None:
            raise NavigationError("invalid_algorithm", f"unknown algorithm {algorithm!r}")

        origin_id = _as_uuid(from_location_id, "from_location_id")
        dest_id = _as_uuid(to_location_id, "to_location_id")
        origin = await self._repo.get_location(origin_id)
        dest = await self._repo.get_location(dest_id)
        if origin is None:
            raise NavigationError("unknown_location", "from_location_id was not found")
        if dest is None:
            raise NavigationError("unknown_location", "to_location_id was not found")
        if origin.id == dest.id:
            raise NavigationError("same_location", "from and to locations are the same")
        if origin.anchor_node is None:
            raise NavigationError("missing_anchor", f"{origin.slug} has no map anchor")
        if dest.anchor_node is None:
            raise NavigationError("missing_anchor", f"{dest.slug} has no map anchor")

        graph = await self._repo.load_mall_graph()
        allow = filter_for(pol)
        if algo in {"bfs", "dfs"}:
            result = router(graph, origin.anchor_node.id, dest.anchor_node.id, allow=allow)
        else:
            result = router(
                graph,
                origin.anchor_node.id,
                dest.anchor_node.id,
                cost_mode=mode,
                allow=allow,
            )
        if not result.ok:
            code = result.failure_reason or "no_path"
            if code == "no_path" and pol is not RouteProfile.NORMAL:
                code = "no_accessible_path"
            raise NavigationError(code, _message_for(code, pol))
        return NavigationRoute(
            result=result,
            instructions=instructions_for(graph, result, destination_name=dest.name),
            floors=floors_on_route(graph, result.node_ids),
            from_location=origin,
            to_location=dest,
            graph=graph,
            profile=pol,
            cost_mode=mode,
        )


def _as_uuid(value: uuid.UUID | str, field: str) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except ValueError as exc:
        raise NavigationError("unknown_location", f"{field} is not a valid id") from exc


def _message_for(code: str, profile: RouteProfile) -> str:
    if code == "no_accessible_path":
        return f"no route under profile {profile.value}"
    if code == "no_path":
        return "no route between these locations"
    if code == "unknown_node":
        return "location anchor is missing from the graph"
    return "routing failed"
