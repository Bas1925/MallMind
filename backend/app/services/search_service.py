"""Hybrid search. Embeddings are skipped when a lexical band already decides."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Literal

from sqlalchemy.exc import SQLAlchemyError

from app.repositories.search_repository import LocationRow, SearchRepository
from app.schemas.search import SearchHitOut, SearchResponse
from app.search.embeddings import EmbeddingError, EmbeddingProvider, vector_literal
from app.search.rank import ScoredHit, allow_semantic_only, lexical_gate, lexical_score, merge_hits
from app.search.text import build_search_text

logger = logging.getLogger(__name__)

# Cosine floor from the 2026-10-06 MiniLM run on NOVA's 31 passages.
# "running shoes" → Nike was 0.435. "withdraw money" → ATM was about 0.444.
# The query "Nike" vs Nike's own passage was 0.388, and vs Adidas was 0.441.
# "مكان للصلاة" peaked at 0.247. "כספומט" peaked at 0.336 on the wrong store.
# 0.38 keeps the paraphrase cluster and Nike's self-match. It does not
# reject "Gucci" (Sushi Kaito was 0.427). The short-query rule does that.
SEMANTIC_MIN_COSINE = 0.38
MAX_QUERY_CHARS = 200


class SearchQueryError(Exception):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass
class _Candidate:
    row: LocationRow
    hit: ScoredHit


class SearchService:
    def __init__(self, repo: SearchRepository, embedder: EmbeddingProvider | None) -> None:
        self._repo = repo
        self._embedder = embedder

    async def search(self, mall_slug: str, query: str, *, limit: int = 8) -> SearchResponse:
        cleaned = " ".join(query.split())
        if cleaned == "":
            raise SearchQueryError("empty_query", "query is empty", 400)
        if len(cleaned) > MAX_QUERY_CHARS:
            raise SearchQueryError("query_too_long", "query is too long", 400)
        mall = await self._repo.get_mall(mall_slug)
        if mall is None:
            raise SearchQueryError("unknown_mall", f"mall {mall_slug!r} was not found", 404)

        rows = await self._repo.lexical_rows(mall.id, cleaned)
        lexical = _lexical_hits(cleaned, rows)
        semantic_state: Literal["used", "skipped", "unavailable"] = "skipped"
        semantic_hits: list[ScoredHit] = []

        lexical_hits = [item.hit for item in lexical]
        # A one- or two-token miss ("Gucci") is a refusal. Do not embed it.
        needs_vectors = (
            not lexical or not lexical_gate(lexical[0].hit.match_type)
        ) and allow_semantic_only(cleaned, lexical_hits)
        if needs_vectors:
            semantic_hits, semantic_state = await self._semantic(mall.id, cleaned)

        merged = merge_hits(
            cleaned,
            lexical_hits,
            semantic_hits,
        )
        by_id = {item.hit.location_id: item.row for item in lexical}
        # Semantic-only rows may be missing from the lexical map when lexical is empty.
        row_by_id = {str(row.id): row for row in rows}
        results: list[SearchHitOut] = []
        for hit in merged[:limit]:
            row = by_id.get(hit.location_id) or row_by_id.get(hit.location_id)
            if row is None:
                continue
            results.append(
                SearchHitOut(
                    location_id=row.id,
                    name=row.name,
                    slug=row.slug,
                    category=row.category_en,
                    category_slug=row.category_slug,
                    floor=row.floor_name,
                    floor_level=row.floor_level,
                    score=round(hit.score, 4),
                    match_type=hit.match_type,
                )
            )
        logger.info(
            "search mall=%s chars=%s lexical=%s semantic=%s returned=%s",
            mall_slug,
            len(cleaned),
            len(lexical),
            semantic_state,
            len(results),
        )
        return SearchResponse(query=cleaned, results=results, semantic=semantic_state)

    async def _semantic(
        self, mall_id: uuid.UUID, query: str
    ) -> tuple[list[ScoredHit], Literal["used", "unavailable"]]:
        if self._embedder is None:
            return [], "unavailable"
        try:
            vector = self._embedder.embed_text(query)
        except EmbeddingError:
            logger.warning(
                "search semantic unavailable model=%s", getattr(self._embedder, "model_name", "?")
            )
            return [], "unavailable"
        try:
            rows = await self._repo.semantic_rows(
                mall_id,
                vector_literal(vector),
                limit=8,
                min_cosine=SEMANTIC_MIN_COSINE,
            )
        except SQLAlchemyError:
            logger.exception("pgvector query failed")
            return [], "unavailable"
        hits = [
            ScoredHit(
                location_id=str(row.location_id),
                slug=row.slug,
                score=row.cosine,
                match_type="semantic",
            )
            for row in rows
        ]
        return hits, "used"


def _lexical_hits(query: str, rows: list[LocationRow]) -> list[_Candidate]:
    found: list[_Candidate] = []
    for row in rows:
        passage = build_search_text(
            name=row.name,
            slug=row.slug,
            description=row.description,
            category_slug=row.category_slug,
            category_en=row.category_en,
            category_he=row.category_he,
            category_ar=row.category_ar,
        )
        scored = lexical_score(
            query,
            name=row.name,
            slug=row.slug,
            category_slug=row.category_slug,
            category_names=(row.category_en, row.category_he, row.category_ar),
            search_text=passage,
            name_similarity=row.name_similarity,
        )
        if scored is None:
            continue
        score, match_type = scored
        found.append(
            _Candidate(
                row=row,
                hit=ScoredHit(
                    location_id=str(row.id),
                    slug=row.slug,
                    score=score,
                    match_type=match_type,
                ),
            )
        )
    found.sort(key=lambda item: (-item.hit.score, item.row.name))
    return found
