"""POST /api/v1/navigation/route"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.repositories.graph_repository import GraphRepository
from app.schemas.navigation import (
    OptimizeRequest,
    OptimizeResponse,
    PlannedSegmentOut,
    PlannedStopOut,
    RouteRequest,
    RouteResponse,
)
from app.services.navigation import NavigationError, NavigationService
from app.services.tour_service import PlannedSegment, PlannedStop, TourPlan, TourService

router = APIRouter(prefix="/navigation", tags=["navigation"])


@router.post("/route")
async def create_route(body: RouteRequest, db: AsyncSession = Depends(get_session)) -> JSONResponse:
    service = NavigationService(db)
    try:
        nav = await service.route(
            body.from_location_id,
            body.to_location_id,
            profile=body.profile,
            cost_mode=body.cost_mode,
            algorithm=body.algorithm,
        )
    except NavigationError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message},
        )
    payload = RouteResponse(
        route=[str(nid) for nid in nav.result.node_ids],
        distance_m=round(nav.result.total_distance_m, 2),
        estimated_seconds=round(nav.result.total_seconds, 2),
        floors=nav.floors,
        instructions=nav.instructions,
        algorithm=nav.result.algorithm,
        nodes_expanded=nav.result.nodes_expanded,
        profile=nav.profile.value,
        from_location=nav.from_location.name,
        to_location=nav.to_location.name,
        node_ids=list(nav.result.node_ids),
        visited_ids=list(nav.result.visited_ids),
    )
    return JSONResponse(status_code=200, content=payload.model_dump(mode="json"))


@router.post("/optimize")
async def optimize_tour(
    body: OptimizeRequest, db: AsyncSession = Depends(get_session)
) -> JSONResponse:
    try:
        profile = body.parsed_profile()
    except ValueError as exc:
        return JSONResponse(
            status_code=400, content={"code": "invalid_profile", "message": str(exc)}
        )
    service = TourService(GraphRepository(db))
    try:
        plan = await service.plan(
            body.start_location_id,
            body.location_ids,
            profile=profile,
            cost_mode=body.cost_mode,
        )
    except NavigationError as exc:
        content: dict[str, object] = {"code": exc.code, "message": exc.message}
        if exc.location_ids:
            content["location_ids"] = exc.location_ids
        return JSONResponse(status_code=exc.status_code, content=content)
    return JSONResponse(status_code=200, content=_optimize_payload(plan).model_dump(mode="json"))


def _optimize_payload(plan: TourPlan) -> OptimizeResponse:
    return OptimizeResponse(
        original_order=_stops(plan.original_order),
        optimized_order=_stops(plan.optimized_order),
        original_distance_m=plan.original_distance_m,
        optimized_distance_m=plan.optimized_distance_m,
        distance_saved_m=plan.distance_saved_m,
        distance_saved_percent=plan.distance_saved_percent,
        original_seconds=plan.original_seconds,
        optimized_seconds=plan.optimized_seconds,
        estimated_time_saved_seconds=plan.estimated_time_saved_seconds,
        floor_changes_original=plan.floor_changes_original,
        floor_changes_optimized=plan.floor_changes_optimized,
        algorithm=plan.algorithm,
        improved=plan.improved,
        message=plan.message,
        segments=[_segment(item) for item in plan.segments],
        node_ids=plan.node_ids,
        instructions=plan.instructions,
        floors=plan.floors,
        profile=plan.profile,
        cost_mode=plan.cost_mode,
        astar_calls=plan.astar_calls,
        two_opt_moves=plan.two_opt_moves,
        nearest_neighbor_distance_m=plan.nearest_neighbor_distance_m,
        nearest_neighbor_2opt_distance_m=plan.nearest_neighbor_2opt_distance_m,
        exact_distance_m=plan.exact_distance_m,
        nearest_neighbor_gap_percent=plan.nearest_neighbor_gap_percent,
        nearest_neighbor_2opt_gap_percent=plan.nearest_neighbor_2opt_gap_percent,
        matrix_m=plan.matrix_m,
        labels=plan.labels,
    )


def _stops(stops: list[PlannedStop]) -> list[PlannedStopOut]:
    return [
        PlannedStopOut(
            location_id=stop.location_id,
            name=stop.name,
            slug=stop.slug,
            floor=stop.floor,
            floor_level=stop.floor_level,
            position=index,
        )
        for index, stop in enumerate(stops, start=1)
    ]


def _segment(segment: PlannedSegment) -> PlannedSegmentOut:
    return PlannedSegmentOut(
        from_location_id=segment.from_location_id,
        to_location_id=segment.to_location_id,
        distance_m=round(segment.distance_m, 1),
        estimated_seconds=round(segment.estimated_seconds, 1),
        floors=segment.floors,
        node_ids=segment.node_ids,
        instructions=segment.instructions,
    )
