"""POST /api/v1/assistant/query"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant.llm import load_llm
from app.assistant.orchestrator import Assistant
from app.assistant.tools import ServiceTools
from app.core.config import settings
from app.core.database import get_session
from app.core.ratelimit import enforce_rate_limit
from app.repositories.search_repository import SearchRepository
from app.schemas.search import AssistantRequest
from app.search.providers import get_embedder
from app.services.navigation import NavigationService
from app.services.search_service import SearchQueryError, SearchService

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/query")
async def query_assistant(
    request: Request,
    body: AssistantRequest,
    db: AsyncSession = Depends(get_session),
) -> JSONResponse:
    limited = enforce_rate_limit(request, scope="assistant", max_calls=20, window_seconds=60)
    if limited is not None:
        return limited
    try:
        profile = body.profile()
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={"code": "invalid_profile", "message": "unknown routing profile"},
        )
    repo = SearchRepository(db)
    search = SearchService(repo, get_embedder())
    assistant = Assistant(
        ServiceTools(search, NavigationService(db), repo),
        load_llm(settings.llm_base_url, settings.llm_api_key, settings.llm_model),
    )
    try:
        payload = await assistant.answer(
            body.message,
            current_location_id=body.current_location_id,
            profile=profile,
        )
    except SearchQueryError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message},
        )
    except ValidationError:
        return JSONResponse(
            status_code=400,
            content={"code": "invalid_request", "message": "could not read the assistant request"},
        )
    return JSONResponse(status_code=200, content=payload.model_dump(mode="json"))
