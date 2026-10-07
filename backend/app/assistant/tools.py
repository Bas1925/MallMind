"""Adapters from assistant tools onto SearchService and NavigationService."""

from __future__ import annotations

import uuid

from app.assistant.orchestrator import RouteFacts
from app.repositories.search_repository import SearchRepository
from app.routing.types import RouteProfile
from app.schemas.search import SearchHitOut
from app.services.navigation import NavigationError, NavigationService
from app.services.search_service import SearchService

MALL_SLUG = "nova-mall"


class ServiceTools:
    def __init__(
        self, search: SearchService, navigation: NavigationService, repo: SearchRepository
    ) -> None:
        self._search = search
        self._navigation = navigation
        self._repo = repo
        self._mall_id: uuid.UUID | None = None

    async def search(self, query: str) -> list[SearchHitOut]:
        payload = await self._search.search(MALL_SLUG, query)
        return payload.results

    async def by_slug(self, slug: str) -> SearchHitOut | None:
        hits = await self.search(slug.replace("-", " "))
        for hit in hits:
            if hit.slug == slug:
                return hit
        return hits[0] if hits else None

    async def by_id(self, location_id: uuid.UUID) -> SearchHitOut | None:
        row = await self._repo.get_location(location_id)
        if row is None:
            return None
        return SearchHitOut(
            location_id=row.id,
            name=row.name,
            slug=row.slug,
            category=row.category.name_en,
            category_slug=row.category.slug,
            floor=row.floor.name,
            floor_level=row.floor.level,
            score=1.0,
            match_type="exact",
        )

    async def route(
        self, origin_id: uuid.UUID, dest_id: uuid.UUID, profile: RouteProfile
    ) -> RouteFacts | None:
        try:
            nav = await self._navigation.route(origin_id, dest_id, profile=profile)
        except NavigationError:
            return None
        return RouteFacts(
            distance_m=nav.result.total_distance_m,
            estimated_seconds=nav.result.total_seconds,
            instructions=nav.instructions,
            floors=nav.floors,
            profile=profile.value,
        )

    async def known_names(self) -> set[str]:
        mall = await self._repo.get_mall(MALL_SLUG)
        if mall is None:
            return set()
        return await self._repo.location_names(mall.id)
