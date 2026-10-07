"""Lexical search, pgvector cosine, and the assistant against seeded PostgreSQL.

Embeddings are off in this suite (EMBEDDING_PROVIDER=none). Semantic quality
is measured by `python -m app.evaluation`, not by CI.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.search_repository import SearchRepository
from app.search.embeddings import HashEmbeddingProvider, vector_literal


@pytest.mark.asyncio
async def test_exact_and_typo(api_client: AsyncClient) -> None:
    exact = await api_client.get("/api/v1/search", params={"q": "Nike"})
    assert exact.status_code == 200, exact.text
    body = exact.json()
    assert body["results"][0]["slug"] == "nike"
    assert body["results"][0]["match_type"] == "exact"
    assert body["semantic"] == "skipped"
    assert "embedding" not in exact.text

    typo = await api_client.get("/api/v1/search", params={"q": "Nkie"})
    assert typo.status_code == 200, typo.text
    assert typo.json()["results"][0]["slug"] == "nike"
    assert typo.json()["results"][0]["match_type"] == "trigram"


@pytest.mark.asyncio
async def test_keyword_category_and_empty(api_client: AsyncClient) -> None:
    shoes = await api_client.get("/api/v1/search", params={"q": "running shoes"})
    assert shoes.status_code == 200, shoes.text
    assert shoes.json()["results"][0]["slug"] == "nike"

    food = await api_client.get("/api/v1/search", params={"q": "food"})
    assert food.status_code == 200
    assert all(row["category_slug"] == "food" for row in food.json()["results"])

    missing = await api_client.get("/api/v1/search", params={"q": "Gucci"})
    assert missing.status_code == 200
    assert missing.json()["results"] == []
    assert missing.json()["semantic"] == "skipped"

    prayer = await api_client.get("/api/v1/search", params={"q": "مكان للصلاة"})
    assert prayer.status_code == 200
    assert prayer.json()["results"] == []

    hebrew = await api_client.get("/api/v1/search", params={"q": "כספומט"})
    assert hebrew.status_code == 200, hebrew.text
    assert hebrew.json()["results"][0]["category_slug"] == "atm"

    empty = await api_client.get("/api/v1/search", params={"q": "   "})
    assert empty.status_code == 400
    assert empty.json()["code"] == "empty_query"

    long = await api_client.get("/api/v1/search", params={"q": "a" * 201})
    assert long.status_code == 400
    assert long.json()["code"] == "query_too_long"


@pytest.mark.asyncio
async def test_assistant_route_and_refusal(api_client: AsyncClient) -> None:
    known = await api_client.post("/api/v1/assistant/query", json={"message": "Where is Nike?"})
    assert known.status_code == 200, known.text
    body = known.json()
    assert body["language"] == "en"
    assert body["sources"][0]["name"] == "Nike"
    assert body["actions"][0]["type"] == "highlight_location"
    assert "search_locations" in body["tools"]

    missing = await api_client.post("/api/v1/assistant/query", json={"message": "Where is Gucci?"})
    assert missing.status_code == 200, missing.text
    assert missing.json()["sources"] == []
    assert "couldn't find" in missing.json()["answer"]

    route = await api_client.post(
        "/api/v1/assistant/query",
        json={"message": "How do I get from the main entrance to Nike?"},
    )
    assert route.status_code == 200, route.text
    payload = route.json()
    assert payload["actions"][0]["type"] == "show_route"
    assert "calculate_route" in payload["tools"]
    assert "m" in payload["answer"]

    arabic = await api_client.post("/api/v1/assistant/query", json={"message": "وين Gucci؟"})
    assert arabic.status_code == 200
    assert arabic.json()["language"] == "ar"
    assert arabic.json()["sources"] == []


@pytest.mark.asyncio
async def test_pgvector_cosine_orders_the_same_vector_first(seeded_session: AsyncSession) -> None:
    repo = SearchRepository(seeded_session)
    mall = await repo.get_mall("nova-mall")
    assert mall is not None
    rows = await repo.lexical_rows(mall.id, "nike")
    nike = next(row for row in rows if row.slug == "nike")
    zara = next(row for row in rows if row.slug == "zara")
    provider = HashEmbeddingProvider()
    nike_vector = provider.embed_text("nike running shoes")
    await repo.upsert_document(
        nike.id, "nike running shoes", "a" * 64, "hash-test", vector_literal(nike_vector)
    )
    await repo.upsert_document(
        zara.id,
        "zara dresses",
        "b" * 64,
        "hash-test",
        vector_literal(provider.embed_text("zara dresses")),
    )
    await seeded_session.flush()
    hits = await repo.semantic_rows(mall.id, vector_literal(nike_vector), limit=5, min_cosine=0.2)
    assert hits
    assert hits[0].slug == "nike"
    assert hits[0].cosine > hits[-1].cosine
