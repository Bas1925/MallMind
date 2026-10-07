"""Search and assistant HTTP payloads. Vectors are never returned."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.routing.types import RouteProfile


class SearchHitOut(BaseModel):
    location_id: uuid.UUID
    name: str
    slug: str
    category: str
    category_slug: str
    floor: str
    floor_level: int
    score: float
    match_type: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchHitOut]
    semantic: Literal["used", "skipped", "unavailable"]


class AssistantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=500)
    current_location_id: uuid.UUID | None = None
    routing_profile: str = "normal"

    def profile(self) -> RouteProfile:
        raw = self.routing_profile.strip().lower()
        if raw == "standard":
            raw = "normal"
        return RouteProfile(raw)


class AssistantSource(BaseModel):
    location_id: uuid.UUID
    name: str
    slug: str
    category_slug: str
    floor: str
    score: float


class AssistantAction(BaseModel):
    type: Literal["highlight_location", "show_route", "change_floor"]
    location_id: uuid.UUID | None = None
    from_location_id: uuid.UUID | None = None
    to_location_id: uuid.UUID | None = None
    floor_level: int | None = None
    profile: str | None = None


class AssistantResponse(BaseModel):
    answer: str
    language: str
    sources: list[AssistantSource]
    actions: list[AssistantAction]
    llm: Literal["template", "provider", "unavailable", "rejected"]
    tools: list[str]
