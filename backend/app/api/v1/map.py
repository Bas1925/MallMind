"""Indoor map + location search. Coordinates match the routing graph."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.repositories.map_repository import MapRepository
from app.schemas.map import LocationSearchResponse
from app.services.map_service import MapNotFoundError, MapService

router = APIRouter(prefix="/malls", tags=["map"])


def _service(db: AsyncSession = Depends(get_session)) -> MapService:
    return MapService(MapRepository(db))


@router.get("/{slug}/map")
async def get_mall_map(slug: str, service: MapService = Depends(_service)) -> JSONResponse:
    try:
        payload = await service.get_map(slug)
    except MapNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"code": "unknown_mall", "message": f"mall {slug!r} was not found"},
        )
    return JSONResponse(status_code=200, content=payload.model_dump(mode="json"))


@router.get("/{slug}/locations")
async def search_locations(
    slug: str,
    q: str = Query(default="", max_length=64),
    service: MapService = Depends(_service),
) -> JSONResponse:
    try:
        results = await service.search(slug, q)
    except MapNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"code": "unknown_mall", "message": f"mall {slug!r} was not found"},
        )
    payload = LocationSearchResponse(results=results)
    return JSONResponse(status_code=200, content=payload.model_dump(mode="json"))
