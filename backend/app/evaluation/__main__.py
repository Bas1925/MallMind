"""python -m app.evaluation

Prints top-1 and top-3 for lexical-only, semantic-only, and hybrid.
Prints assistant grounding against the live database.
Does not invent a score when a mode cannot run.
"""

from __future__ import annotations

import asyncio
import sys

from app.assistant.llm import load_llm
from app.assistant.orchestrator import Assistant
from app.assistant.tools import ServiceTools
from app.core.config import settings
from app.core.database import SessionLocal
from app.evaluation.cases import ASSISTANT_CASES, SEARCH_CASES, SearchCase
from app.repositories.search_repository import SearchRepository
from app.routing.types import RouteProfile
from app.schemas.search import SearchHitOut
from app.search.providers import get_embedder
from app.search.rank import ScoredHit, merge_hits
from app.services.navigation import NavigationService
from app.services.search_service import SearchService, _lexical_hits


def _hit_ok(hit: SearchHitOut | None, case: SearchCase) -> bool:
    if case.accept_slugs is None and case.accept_category is None:
        return hit is None
    if hit is None:
        return False
    if case.accept_slugs is not None and hit.slug in case.accept_slugs:
        return True
    return case.accept_category is not None and hit.category_slug == case.accept_category


def _summarize(label: str, cases: list[SearchCase], columns: list[list[SearchHitOut]]) -> None:
    top1 = 0
    top3 = 0
    for case, hits in zip(cases, columns, strict=True):
        expects_empty = case.accept_slugs is None and case.accept_category is None
        if expects_empty:
            ok = len(hits) == 0
            top1 += int(ok)
            top3 += int(ok)
        else:
            if _hit_ok(hits[0] if hits else None, case):
                top1 += 1
            if any(_hit_ok(hit, case) for hit in hits[:3]):
                top3 += 1
        head = hits[0].slug if hits else "-"
        print(f"  {case.query!r:40} {head:20} {case.note}")
    n = len(cases)
    print(f"{label}: top1 {top1}/{n}  top3 {top3}/{n}")


async def _run() -> int:
    embedder = get_embedder()
    async with SessionLocal() as session:
        repo = SearchRepository(session)
        mall = await repo.get_mall("nova-mall")
        if mall is None:
            print("nova-mall is not seeded", file=sys.stderr)
            return 1
        search = SearchService(repo, embedder)
        lexical_cols: list[list[SearchHitOut]] = []
        semantic_cols: list[list[SearchHitOut]] = []
        hybrid_cols: list[list[SearchHitOut]] = []
        semantic_ran = embedder is not None
        for case in SEARCH_CASES:
            rows = await repo.lexical_rows(mall.id, case.query)
            lexical = _lexical_hits(case.query, rows)
            lexical_hits = [_to_out(item.row, item.hit) for item in lexical]
            lexical_cols.append(lexical_hits)
            semantic_hits: list[ScoredHit] = []
            if embedder is not None:
                semantic_hits, state = await search._semantic(mall.id, case.query)
                if state != "used":
                    semantic_ran = False
            row_by_id = {str(row.id): row for row in rows}
            semantic_out = [
                _to_out(row_by_id[hit.location_id], hit)
                for hit in semantic_hits
                if hit.location_id in row_by_id
            ]
            semantic_cols.append(semantic_out)
            merged = merge_hits(case.query, [item.hit for item in lexical], semantic_hits)
            hybrid_cols.append(
                [
                    _to_out(row_by_id[hit.location_id], hit)
                    for hit in merged
                    if hit.location_id in row_by_id
                ]
            )
        print("lexical")
        _summarize("lexical", list(SEARCH_CASES), lexical_cols)
        if semantic_ran:
            print("semantic")
            _summarize("semantic", list(SEARCH_CASES), semantic_cols)
        else:
            print("semantic: unavailable (no embedder, or the provider failed)")
        print("hybrid")
        _summarize("hybrid", list(SEARCH_CASES), hybrid_cols)

        assistant = Assistant(
            ServiceTools(search, NavigationService(session), repo),
            load_llm(settings.llm_base_url, settings.llm_api_key, settings.llm_model),
        )
        grounded = 0
        for case in ASSISTANT_CASES:
            result = await assistant.answer(
                case.message, current_location_id=None, profile=RouteProfile.NORMAL
            )
            ok = _assistant_ok(case, result.sources, result.actions, result.answer, result.language)
            grounded += int(ok)
            print(
                f"  assistant {case.message!r:48} lang={result.language} tools={result.tools} "
                f"ok={ok} llm={result.llm}"
            )
        print(f"assistant grounding: {grounded}/{len(ASSISTANT_CASES)}")
        if not settings.llm_api_key:
            print("live llm: pending (LLM_API_KEY is not set; answers are templates)")
    return 0


def _assistant_ok(case, sources, actions, answer: str, language: str) -> bool:
    del answer
    if language != case.language:
        return False
    if case.expect == "refusal":
        return sources == [] and actions == []
    if case.expect == "slug":
        return case.accept_slug is not None and any(
            source.slug == case.accept_slug for source in sources
        )
    if case.expect == "category":
        return case.accept_category is not None and any(
            source.category_slug == case.accept_category for source in sources
        )
    if case.expect == "route":
        routes = [action for action in actions if action.type == "show_route"]
        if not routes:
            return False
        if case.profile is not None and routes[0].profile != case.profile:
            return False
        if case.accept_slug is None:
            return True
        return any(source.slug == case.accept_slug for source in sources)
    return False


def _to_out(row, hit: ScoredHit) -> SearchHitOut:
    return SearchHitOut(
        location_id=row.id,
        name=row.name,
        slug=row.slug,
        category=row.category_en,
        category_slug=row.category_slug,
        floor=row.floor_name,
        floor_level=row.floor_level,
        score=hit.score,
        match_type=hit.match_type,
    )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(asyncio.run(_run()))
