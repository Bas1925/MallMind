"""GET /api/v1/malls/{slug}/map against a real seeded PostgreSQL."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_map_payload_shape(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/malls/nova-mall/map")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["mall"]["slug"] == "nova-mall"
    assert len(body["floors"]) == 3
    assert len(body["locations"]) == 31
    assert len(body["nodes"]) == 91
    assert len(body["edges"]) == 248
    nike = next(loc for loc in body["locations"] if loc["slug"] == "nike")
    assert nike["x"] is not None
    assert nike["floor_level"] == 0
    assert nike["category_slug"] == "fashion"
    hallway = next(edge for edge in body["edges"] if edge["edge_type"] == "hallway")
    assert hallway["from_floor_level"] == hallway["to_floor_level"]
    elevator = next(edge for edge in body["edges"] if edge["edge_type"] == "elevator")
    assert elevator["from_floor_level"] != elevator["to_floor_level"]


@pytest.mark.asyncio
async def test_unknown_mall(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/malls/no-such-mall/map")
    assert response.status_code == 404
    assert response.json()["code"] == "unknown_mall"


@pytest.mark.asyncio
async def test_location_search(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/malls/nova-mall/locations", params={"q": "nike"})
    assert response.status_code == 200, response.text
    names = [row["name"] for row in response.json()["results"]]
    assert "Nike" in names
    bathroom = await api_client.get("/api/v1/malls/nova-mall/locations", params={"q": "bathroom"})
    assert bathroom.status_code == 200
    slugs = [row["slug"] for row in bathroom.json()["results"]]
    assert any(slug.startswith("restroom") for slug in slugs)
