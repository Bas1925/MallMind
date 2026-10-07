"""GET /api/v1/search — lexical first, vectors only when the name is not obvious."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.ratelimit import enforce_rate_limit
from app.repositories.search_repository import SearchRepository
from app.search.providers import get_embedder
from app.services.search_service import SearchQueryError, SearchService

router = APIRouter(prefix="/search", tags=["search"])


def _service(db: AsyncSession = Depends(get_session)) -> SearchService:
    return SearchService(SearchRepository(db), get_embedder())


@router.get("")
async def search_locations(
    request: Request,
    q: str = Query(default=""),
    mall: str = Query(default="nova-mall", max_length=64),
    service: SearchService = Depends(_service),
) -> JSONResponse:
    limited = enforce_rate_limit(request, scope="search", max_calls=60, window_seconds=60)
    if limited is not None:
        return limited
    try:
        payload = await service.search(mall, q)
    except SearchQueryError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message},
        )
    return JSONResponse(status_code=200, content=payload.model_dump(mode="json"))
