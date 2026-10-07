"""Mall assistant.

Tool choice is code. Route geometry is NavigationService. The language model,
when one is configured, only phrases location facts we already retrieved.
Route numbers stay on the template so a model cannot invent a distance.
If the model is down or ungrounded, the template still answers.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Literal, Protocol

from app.assistant.compose import (
    RouteCopy,
    answer_is_grounded,
    choices_answer,
    here_answer,
    location_answer,
    missing_start_answer,
    no_route_answer,
    refusal_answer,
    route_answer,
)
from app.assistant.intent import parse_intent
from app.assistant.llm import SYSTEM_PROMPT, LlmClient, LlmError
from app.routing.types import RouteProfile
from app.schemas.search import AssistantAction, AssistantResponse, AssistantSource, SearchHitOut
from app.search.language import detect_language

logger = logging.getLogger(__name__)

LlmMode = Literal["template", "provider", "unavailable", "rejected"]


@dataclass(frozen=True)
class RouteFacts:
    distance_m: float
    estimated_seconds: float
    instructions: list[str]
    floors: list[int]
    profile: str


class AssistantTools(Protocol):
    async def search(self, query: str) -> list[SearchHitOut]: ...

    async def by_slug(self, slug: str) -> SearchHitOut | None: ...

    async def by_id(self, location_id: uuid.UUID) -> SearchHitOut | None: ...

    async def route(
        self, origin_id: uuid.UUID, dest_id: uuid.UUID, profile: RouteProfile
    ) -> RouteFacts | None: ...

    async def known_names(self) -> set[str]: ...


class Assistant:
    def __init__(self, tools: AssistantTools, llm: LlmClient | None) -> None:
        self._tools = tools
        self._llm = llm

    async def answer(
        self,
        message: str,
        *,
        current_location_id: uuid.UUID | None,
        profile: RouteProfile,
    ) -> AssistantResponse:
        started = time.perf_counter()
        language = detect_language(message)
        intent = parse_intent(message, profile)
        tools_used: list[str] = []
        if intent.kind == "route":
            response = await self._route(
                language,
                intent.destination_query or intent.query,
                intent.origin_query,
                current_location_id,
                intent.profile,
                tools_used,
            )
        elif intent.kind == "nearest":
            response = await self._nearest(
                language, intent.query, current_location_id, intent.profile, tools_used
            )
        elif intent.kind == "here":
            response = await self._here(language, current_location_id, tools_used)
        else:
            response = await self._search(language, intent.query, tools_used)
        logger.info(
            "assistant lang=%s tools=%s sources=%s llm=%s ms=%s chars=%s",
            response.language,
            ",".join(tools_used) or "-",
            len(response.sources),
            response.llm,
            int((time.perf_counter() - started) * 1000),
            len(message),
        )
        return response

    async def _here(
        self,
        language: str,
        current_location_id: uuid.UUID | None,
        tools_used: list[str],
    ) -> AssistantResponse:
        if current_location_id is None:
            return AssistantResponse(
                answer=missing_start_answer(language),
                language=language,
                sources=[],
                actions=[],
                llm="template",
                tools=tools_used,
            )
        tools_used.append("get_location")
        hit = await self._tools.by_id(current_location_id)
        if hit is None:
            return _refuse(language, tools_used)
        actions = [
            AssistantAction(
                type="highlight_location",
                location_id=hit.location_id,
                floor_level=hit.floor_level,
            ),
            AssistantAction(type="change_floor", floor_level=hit.floor_level),
        ]
        return await self._finish(language, here_answer(language, hit), [hit], actions, tools_used)

    async def _search(self, language: str, query: str, tools_used: list[str]) -> AssistantResponse:
        tools_used.append("search_locations")
        hits = await self._tools.search(query)
        if not hits:
            return _refuse(language, tools_used)
        top = hits[0]
        if len(hits) > 1 and top.match_type == "category":
            actions = [
                AssistantAction(
                    type="highlight_location",
                    location_id=top.location_id,
                    floor_level=top.floor_level,
                ),
                AssistantAction(type="change_floor", floor_level=top.floor_level),
            ]
            return await self._finish(
                language, choices_answer(language, hits), hits[:3], actions, tools_used
            )
        actions = [
            AssistantAction(
                type="highlight_location",
                location_id=top.location_id,
                floor_level=top.floor_level,
            ),
            AssistantAction(type="change_floor", floor_level=top.floor_level),
        ]
        return await self._finish(
            language, location_answer(language, top), [top], actions, tools_used
        )

    async def _nearest(
        self,
        language: str,
        facility: str,
        current_location_id: uuid.UUID | None,
        profile: RouteProfile,
        tools_used: list[str],
    ) -> AssistantResponse:
        tools_used.append("search_locations")
        hits = await self._tools.search(facility)
        if not hits:
            return _refuse(language, tools_used)
        origin = await self._origin(None, current_location_id, tools_used)
        if origin is None:
            return await self._finish(
                language,
                location_answer(language, hits[0]),
                [hits[0]],
                [
                    AssistantAction(
                        type="highlight_location",
                        location_id=hits[0].location_id,
                        floor_level=hits[0].floor_level,
                    )
                ],
                tools_used,
            )
        tools_used.append("calculate_route")
        best_hit: SearchHitOut | None = None
        best_route: RouteFacts | None = None
        for hit in hits[:4]:
            if hit.location_id == origin.location_id:
                continue
            routed = await self._tools.route(origin.location_id, hit.location_id, profile)
            if routed is None:
                continue
            if best_route is None or routed.distance_m < best_route.distance_m:
                best_hit = hit
                best_route = routed
        if best_hit is None or best_route is None:
            return _no_route(language, origin.name, hits[0].name, tools_used)
        return _route_response(language, origin, best_hit, best_route, tools_used)

    async def _route(
        self,
        language: str,
        destination_query: str,
        origin_query: str | None,
        current_location_id: uuid.UUID | None,
        profile: RouteProfile,
        tools_used: list[str],
    ) -> AssistantResponse:
        tools_used.append("search_locations")
        found = await self._tools.search(destination_query)
        if not found:
            return _refuse(language, tools_used)
        dest = found[0]
        origin = await self._origin(origin_query, current_location_id, tools_used)
        if origin is None:
            return _refuse(language, tools_used)
        if origin.location_id == dest.location_id:
            return await self._finish(
                language,
                location_answer(language, dest),
                [dest],
                [
                    AssistantAction(
                        type="highlight_location",
                        location_id=dest.location_id,
                        floor_level=dest.floor_level,
                    )
                ],
                tools_used,
                allow_llm=False,
            )
        tools_used.append("calculate_route")
        routed = await self._tools.route(origin.location_id, dest.location_id, profile)
        if routed is None:
            return _no_route(language, origin.name, dest.name, tools_used)
        return _route_response(language, origin, dest, routed, tools_used)

    async def _origin(
        self,
        origin_query: str | None,
        current_location_id: uuid.UUID | None,
        tools_used: list[str],
    ) -> SearchHitOut | None:
        if origin_query:
            tools_used.append("search_locations")
            found = await self._tools.search(origin_query)
            return found[0] if found else None
        if current_location_id is not None:
            tools_used.append("get_location")
            return await self._tools.by_id(current_location_id)
        return await self._tools.by_slug("main-entrance")

    async def _finish(
        self,
        language: str,
        template: str,
        hits: list[SearchHitOut],
        actions: list[AssistantAction],
        tools_used: list[str],
        *,
        allow_llm: bool = True,
    ) -> AssistantResponse:
        answer = template
        mode: LlmMode = "template"
        if allow_llm and self._llm is not None and hits:
            phrased = await self._phrase(template, hits)
            if phrased is None:
                mode = "unavailable"
            elif phrased == "":
                mode = "rejected"
            else:
                answer = phrased
                mode = "provider"
        return AssistantResponse(
            answer=answer,
            language=language,
            sources=_sources(hits),
            actions=actions,
            llm=mode,
            tools=tools_used,
        )

    async def _phrase(self, template: str, hits: list[SearchHitOut]) -> str | None:
        """Return phrased text, '' if rejected, None if the provider failed."""
        facts = {
            "language": detect_language(template),
            "template": template,
            "locations": [
                {"name": hit.name, "category": hit.category, "floor": hit.floor} for hit in hits
            ],
        }
        assert self._llm is not None
        try:
            text = self._llm.complete(SYSTEM_PROMPT, json.dumps(facts, ensure_ascii=False))
        except LlmError:
            logger.warning("assistant llm failed; using template")
            return None
        known = await self._tools.known_names()
        if not answer_is_grounded(text, {hit.name for hit in hits}, known):
            logger.warning("assistant llm rejected ungrounded text")
            return ""
        return text


def _route_response(
    language: str,
    origin: SearchHitOut,
    dest: SearchHitOut,
    routed: RouteFacts,
    tools_used: list[str],
) -> AssistantResponse:
    instruction = routed.instructions[0] if routed.instructions else ""
    text = route_answer(
        language,
        RouteCopy(
            origin=origin.name,
            destination=dest.name,
            distance_m=routed.distance_m,
            estimated_seconds=routed.estimated_seconds,
            instruction=instruction,
            profile=routed.profile,
        ),
    )
    return AssistantResponse(
        answer=text,
        language=language,
        sources=_sources([origin, dest]),
        actions=[
            AssistantAction(
                type="show_route",
                from_location_id=origin.location_id,
                to_location_id=dest.location_id,
                profile=routed.profile,
                floor_level=origin.floor_level,
            ),
            AssistantAction(type="change_floor", floor_level=origin.floor_level),
            AssistantAction(
                type="highlight_location",
                location_id=dest.location_id,
                floor_level=dest.floor_level,
            ),
        ],
        llm="template",
        tools=tools_used,
    )


def _refuse(language: str, tools_used: list[str]) -> AssistantResponse:
    return AssistantResponse(
        answer=refusal_answer(language),
        language=language,
        sources=[],
        actions=[],
        llm="template",
        tools=tools_used,
    )


def _no_route(
    language: str, origin: str, destination: str, tools_used: list[str]
) -> AssistantResponse:
    return AssistantResponse(
        answer=no_route_answer(language, origin, destination),
        language=language,
        sources=[],
        actions=[],
        llm="template",
        tools=tools_used,
    )


def _sources(hits: list[SearchHitOut]) -> list[AssistantSource]:
    seen: set[uuid.UUID] = set()
    sources: list[AssistantSource] = []
    for hit in hits:
        if hit.location_id in seen:
            continue
        seen.add(hit.location_id)
        sources.append(
            AssistantSource(
                location_id=hit.location_id,
                name=hit.name,
                slug=hit.slug,
                category_slug=hit.category_slug,
                floor=hit.floor,
                score=hit.score,
            )
        )
    return sources
