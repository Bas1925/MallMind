"""Pydantic payloads for the navigation API."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.routing.types import CostMode, RouteProfile


class RouteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_location_id: uuid.UUID
    to_location_id: uuid.UUID
    profile: RouteProfile = RouteProfile.NORMAL
    cost_mode: CostMode = CostMode.DISTANCE


class OptimizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_location_id: uuid.UUID
    location_ids: list[uuid.UUID] = Field(default_factory=list)
    profile: str = "normal"
    cost_mode: CostMode = CostMode.DISTANCE

    def parsed_profile(self) -> RouteProfile:
        raw = self.profile.strip().lower()
        if raw == "standard":
            raw = "normal"
        try:
            return RouteProfile(raw)
        except ValueError as exc:
            raise ValueError(f"unknown profile {self.profile!r}") from exc


class PlannedStopOut(BaseModel):
    location_id: uuid.UUID
    name: str
    slug: str
    floor: str
    floor_level: int
    position: int


class PlannedSegmentOut(BaseModel):
    from_location_id: uuid.UUID
    to_location_id: uuid.UUID
    distance_m: float
    estimated_seconds: float
    floors: list[int]
    node_ids: list[uuid.UUID]
    instructions: list[str]


class OptimizeResponse(BaseModel):
    original_order: list[PlannedStopOut]
    optimized_order: list[PlannedStopOut]
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
    segments: list[PlannedSegmentOut]
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


class RouteResponse(BaseModel):
    route: list[str]
    distance_m: float
    estimated_seconds: float
    floors: list[int]
    instructions: list[str]
    algorithm: str
    nodes_expanded: int
    profile: str
    from_location: str
    to_location: str
    node_ids: list[uuid.UUID] = Field(default_factory=list)
