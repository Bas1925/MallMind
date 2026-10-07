"""Assistant behavior with fake tools and a fake model. No paid API."""

from __future__ import annotations

import uuid

import pytest

from app.assistant.compose import answer_is_grounded
from app.assistant.llm import LlmError
from app.assistant.orchestrator import Assistant, RouteFacts
from app.routing.types import RouteProfile
from app.schemas.search import SearchHitOut


def _hit(name: str, slug: str, category: str, floor: str = "Ground Floor") -> SearchHitOut:
    return SearchHitOut(
        location_id=uuid.uuid4(),
        name=name,
        slug=slug,
        category=category,
        category_slug=category.casefold(),
        floor=floor,
        floor_level=0,
        score=1.0,
        match_type="exact",
    )


NIKE = _hit("Nike", "nike", "Fashion")
ENTRANCE = _hit("Main Entrance", "main-entrance", "Entrance")
RESTROOM = _hit("Restroom — Ground North", "restroom-g-north", "Restroom")


class FakeTools:
    def __init__(self, *, route: RouteFacts | None) -> None:
        self.route_calls: list[tuple[uuid.UUID, uuid.UUID, str]] = []
        self.queries: list[str] = []
        self._route = route

    async def search(self, query: str) -> list[SearchHitOut]:
        self.queries.append(query)
        folded = query.casefold()
        if "gucci" in folded:
            return []
        if "nike" in folded:
            return [NIKE]
        if "bathroom" in folded or "حمام" in query:
            return [RESTROOM]
        if "entrance" in folded or "main" in folded:
            return [ENTRANCE]
        if "atm" in folded or "כספומט" in query:
            atm = _hit("ATM — Ground", "atm-g", "ATM")
            atm_copy = atm.model_copy(update={"match_type": "category"})
            return [atm_copy]
        return []

    async def by_slug(self, slug: str) -> SearchHitOut | None:
        if slug == "main-entrance":
            return ENTRANCE
        return None

    async def by_id(self, location_id: uuid.UUID) -> SearchHitOut | None:
        if location_id == NIKE.location_id:
            return NIKE
        return None

    async def route(
        self, origin_id: uuid.UUID, dest_id: uuid.UUID, profile: RouteProfile
    ) -> RouteFacts | None:
        self.route_calls.append((origin_id, dest_id, profile.value))
        return self._route

    async def known_names(self) -> set[str]:
        return {"Nike", "Zara", "Main Entrance"}


class FakeLlm:
    def __init__(self, text: str | None, *, fail: bool = False) -> None:
        self.text = text
        self.fail = fail
        self.calls = 0

    def complete(self, system: str, user: str) -> str:
        self.calls += 1
        del system, user
        if self.fail:
            raise LlmError("down")
        assert self.text is not None
        return self.text


def _route() -> RouteFacts:
    return RouteFacts(102.0, 90.0, ["Walk 102 m"], [0], "normal")


@pytest.mark.asyncio
async def test_known_store_uses_search_not_model_when_unconfigured() -> None:
    assistant = Assistant(FakeTools(route=_route()), None)
    result = await assistant.answer(
        "Where is Nike?", current_location_id=None, profile=RouteProfile.NORMAL
    )
    assert result.language == "en"
    assert result.sources[0].name == "Nike"
    assert result.actions[0].type == "highlight_location"
    assert result.llm == "template"
    assert "Ground Floor" in result.answer


@pytest.mark.asyncio
async def test_unknown_store_refuses_in_three_languages() -> None:
    assistant = Assistant(FakeTools(route=_route()), FakeLlm("Gucci is on floor 2", fail=False))
    for message, language, snippet in (
        ("Where is Gucci?", "en", "couldn't find"),
        ("وين Gucci؟", "ar", "ما لقيت"),
        ("איפה Gucci?", "he", "לא מצאתי"),
    ):
        result = await assistant.answer(
            message, current_location_id=None, profile=RouteProfile.NORMAL
        )
        assert result.language == language
        assert result.sources == []
        assert snippet in result.answer


@pytest.mark.asyncio
async def test_route_comes_from_the_tool() -> None:
    tools = FakeTools(route=_route())
    llm = FakeLlm("The walk is 1 meter via a secret corridor.")
    assistant = Assistant(tools, llm)
    result = await assistant.answer(
        "How do I get from the main entrance to Nike?",
        current_location_id=None,
        profile=RouteProfile.NORMAL,
    )
    assert tools.route_calls
    assert result.actions[0].type == "show_route"
    assert "102" in result.answer
    assert "secret" not in result.answer
    assert llm.calls == 0


@pytest.mark.asyncio
async def test_avoid_stairs_profile_is_sent() -> None:
    tools = FakeTools(route=RouteFacts(110.0, 100.0, ["Take the elevator"], [0, 1], "avoid_stairs"))
    assistant = Assistant(tools, None)
    result = await assistant.answer(
        "How can I reach Nike without stairs?",
        current_location_id=None,
        profile=RouteProfile.NORMAL,
    )
    assert tools.route_calls[0][2] == "avoid_stairs"
    assert result.actions[0].profile == "avoid_stairs"


@pytest.mark.asyncio
async def test_no_route() -> None:
    assistant = Assistant(FakeTools(route=None), None)
    result = await assistant.answer(
        "Take me to Nike",
        current_location_id=None,
        profile=RouteProfile.NORMAL,
    )
    assert "no route" in result.answer.casefold()
    assert result.actions == []


@pytest.mark.asyncio
async def test_provider_failure_falls_back_to_template() -> None:
    llm = FakeLlm(None, fail=True)
    assistant = Assistant(FakeTools(route=_route()), llm)
    result = await assistant.answer(
        "Where is Nike?", current_location_id=None, profile=RouteProfile.NORMAL
    )
    assert result.llm == "unavailable"
    assert "Nike" in result.answer
    assert "Ground Floor" in result.answer


@pytest.mark.asyncio
async def test_malformed_provider_text_is_rejected() -> None:
    llm = FakeLlm("Nike is next to Gucci on Floor 9.")
    assistant = Assistant(FakeTools(route=_route()), llm)
    result = await assistant.answer(
        "Where is Nike?", current_location_id=None, profile=RouteProfile.NORMAL
    )
    assert result.llm == "rejected"
    assert "Gucci" not in result.answer
    assert "Ground Floor" in result.answer


@pytest.mark.asyncio
async def test_hebrew_atm_searches_the_facility_word() -> None:
    tools = FakeTools(route=_route())
    assistant = Assistant(tools, None)
    result = await assistant.answer(
        "איפה הכספומט?", current_location_id=None, profile=RouteProfile.NORMAL
    )
    assert tools.queries == ["atm"]
    assert result.language == "he"
    assert result.sources[0].slug == "atm-g"


@pytest.mark.asyncio
async def test_where_did_i_start_uses_the_current_location() -> None:
    assistant = Assistant(FakeTools(route=_route()), None)
    result = await assistant.answer(
        "Where did I start?",
        current_location_id=NIKE.location_id,
        profile=RouteProfile.NORMAL,
    )
    assert result.sources[0].slug == "nike"
    assert "Nike" in result.answer
    assert "get_location" in result.tools
    assert result.llm == "template"


@pytest.mark.asyncio
async def test_where_did_i_start_without_a_point() -> None:
    assistant = Assistant(FakeTools(route=_route()), None)
    result = await assistant.answer(
        "Where did I start?", current_location_id=None, profile=RouteProfile.NORMAL
    )
    assert result.sources == []
    assert "starting point" in result.answer


def test_dead_llm_endpoint_is_an_error() -> None:
    from app.assistant.llm import OpenAICompatibleChat

    client = OpenAICompatibleChat(
        base_url="http://127.0.0.1:9", api_key="not-a-real-key", model="x"
    )
    with pytest.raises(LlmError):
        client.complete("system", "hello")


def test_grounding_blocks_other_mall_stores() -> None:
    assert answer_is_grounded("Nike is on Ground Floor.", {"Nike"}, {"Nike", "Zara"})
    assert not answer_is_grounded("Try Zara instead.", {"Nike"}, {"Nike", "Zara"})
