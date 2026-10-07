"""Build search passages and embeddings.

Usage:

    python -m app.search.reindex

A row is skipped when the passage hash, model name, and stored vector all
match. A failed embed call does not erase a vector already stored.
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Mall
from app.repositories.search_repository import SearchRepository
from app.search.embeddings import EmbeddingError, vector_literal
from app.search.providers import get_embedder
from app.search.text import build_search_text, content_hash


async def reindex() -> int:
    embedder = get_embedder()
    model_name = embedder.model_name if embedder is not None else "none"
    written = 0
    skipped = 0
    embed_failures = 0
    async with SessionLocal() as session:
        repo = SearchRepository(session)
        malls = list((await session.scalars(select(Mall))).all())
        if not malls:
            print("no malls to index", file=sys.stderr)
            return 1
        for mall in malls:
            rows = await repo.lexical_rows(mall.id, " ")
            existing = await repo.list_documents(mall.id)
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
                digest = content_hash(model_name, passage)
                previous = existing.get(row.id)
                if (
                    previous is not None
                    and previous[0] == digest
                    and previous[1] == model_name
                    and await repo.embedding_present(row.id)
                ):
                    skipped += 1
                    continue
                vector: str | None = None
                stored_model: str | None = None
                if embedder is not None:
                    try:
                        vector = vector_literal(embedder.embed_text(passage))
                        stored_model = model_name
                    except EmbeddingError as exc:
                        embed_failures += 1
                        print(f"embed failed {row.slug}: {exc}", file=sys.stderr)
                await repo.upsert_document(row.id, passage, digest, stored_model, vector)
                written += 1
        await session.commit()
    print(
        f"reindex model={model_name} written={written} skipped={skipped} "
        f"embed_failures={embed_failures}"
    )
    return 0 if embed_failures == 0 else 2


def main() -> None:
    raise SystemExit(asyncio.run(reindex()))


if __name__ == "__main__":
    main()
