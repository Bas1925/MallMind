"""Lexical similarities and pgvector cosine lookup."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Location, LocationDocument, Mall


@dataclass(frozen=True)
class LocationRow:
    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    category_slug: str
    category_en: str
    category_he: str
    category_ar: str
    floor_level: int
    floor_name: str
    name_similarity: float


@dataclass(frozen=True)
class SemanticRow:
    location_id: uuid.UUID
    slug: str
    cosine: float


class SearchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_mall(self, slug: str) -> Mall | None:
        return await self._session.scalar(select(Mall).where(Mall.slug == slug))

    async def lexical_rows(self, mall_id: uuid.UUID, query: str) -> list[LocationRow]:
        sql = text(
            """
            SELECT
                l.id,
                l.slug,
                l.name,
                l.description,
                c.slug AS category_slug,
                c.name_en,
                c.name_he,
                c.name_ar,
                f.level,
                f.name AS floor_name,
                similarity(lower(l.name), lower(:query)) AS name_sim
            FROM locations l
            JOIN categories c ON c.id = l.category_id
            JOIN floors f ON f.id = l.floor_id
            WHERE l.mall_id = :mall_id
              AND l.is_active
            """
        )
        result = await self._session.execute(sql, {"mall_id": mall_id, "query": query})
        rows: list[LocationRow] = []
        for record in result.mappings():
            rows.append(
                LocationRow(
                    id=record["id"],
                    slug=record["slug"],
                    name=record["name"],
                    description=record["description"],
                    category_slug=record["category_slug"],
                    category_en=record["name_en"],
                    category_he=record["name_he"],
                    category_ar=record["name_ar"],
                    floor_level=int(record["level"]),
                    floor_name=record["floor_name"],
                    name_similarity=float(record["name_sim"] or 0.0),
                )
            )
        return rows

    async def semantic_rows(
        self,
        mall_id: uuid.UUID,
        vector_literal: str,
        *,
        limit: int,
        min_cosine: float,
    ) -> list[SemanticRow]:
        sql = text(
            """
            SELECT l.id AS location_id,
                   l.slug,
                   1 - (d.embedding <=> CAST(:vector AS vector)) AS cosine
            FROM location_documents d
            JOIN locations l ON l.id = d.location_id
            WHERE l.mall_id = :mall_id
              AND l.is_active
              AND d.embedding IS NOT NULL
              AND 1 - (d.embedding <=> CAST(:vector AS vector)) >= :min_cosine
            ORDER BY d.embedding <=> CAST(:vector AS vector)
            LIMIT :limit
            """
        )
        result = await self._session.execute(
            sql,
            {
                "mall_id": mall_id,
                "vector": vector_literal,
                "limit": limit,
                "min_cosine": min_cosine,
            },
        )
        return [
            SemanticRow(
                location_id=record["location_id"],
                slug=record["slug"],
                cosine=float(record["cosine"]),
            )
            for record in result.mappings()
        ]

    async def list_documents(self, mall_id: uuid.UUID) -> dict[uuid.UUID, tuple[str, str | None]]:
        result = await self._session.execute(
            select(
                LocationDocument.location_id,
                LocationDocument.content_hash,
                LocationDocument.embedding_model,
            )
            .join(Location, Location.id == LocationDocument.location_id)
            .where(Location.mall_id == mall_id)
        )
        return {row[0]: (str(row[1]).strip(), row[2]) for row in result.all()}

    async def embedding_present(self, location_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            text("SELECT embedding IS NOT NULL FROM location_documents WHERE location_id = :id"),
            {"id": location_id},
        )
        value = result.scalar_one_or_none()
        return bool(value)

    async def upsert_document(
        self,
        location_id: uuid.UUID,
        search_text: str,
        content_hash: str,
        embedding_model: str | None,
        vector_literal: str | None,
    ) -> None:
        await self._session.execute(
            text(
                """
                INSERT INTO location_documents (
                    location_id, search_text, content_hash, embedding_model, embedding, updated_at
                )
                VALUES (
                    :location_id,
                    :search_text,
                    :content_hash,
                    :embedding_model,
                    CAST(:embedding AS vector),
                    now()
                )
                ON CONFLICT (location_id) DO UPDATE SET
                    search_text = EXCLUDED.search_text,
                    content_hash = EXCLUDED.content_hash,
                    embedding_model = EXCLUDED.embedding_model,
                    embedding = COALESCE(EXCLUDED.embedding, location_documents.embedding),
                    updated_at = now()
                """
            ),
            {
                "location_id": location_id,
                "search_text": search_text,
                "content_hash": content_hash,
                "embedding_model": embedding_model,
                "embedding": vector_literal,
            },
        )

    async def location_names(self, mall_id: uuid.UUID) -> set[str]:
        result = await self._session.scalars(
            select(Location.name).where(Location.mall_id == mall_id, Location.is_active.is_(True))
        )
        return set(result.all())

    async def get_location(self, location_id: uuid.UUID) -> Location | None:
        return await self._session.scalar(
            select(Location)
            .options(selectinload(Location.category), selectinload(Location.floor))
            .where(Location.id == location_id, Location.is_active.is_(True))
        )
