"""Domain operations for seeding a mall.

Validates first, then writes. Never repairs invalid data.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Mall
from app.repositories.seed_repository import SeedRepository
from app.schemas.seed import SeedDocument
from app.seed.validator import assert_valid


class SeedAlreadyAppliedError(RuntimeError):
    """The mall slug is already present and `--force` was not given."""


class SeedService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = SeedRepository(session)

    async def apply(self, doc: SeedDocument, *, force: bool = False) -> Mall:
        assert_valid(doc)
        existing = await self._repo.get_mall_by_slug(doc.mall.slug)
        if existing is not None:
            if not force:
                raise SeedAlreadyAppliedError(
                    f"mall {doc.mall.slug!r} is already seeded; pass --force to replace it"
                )
            await self._repo.delete_mall_graph(existing)
        return await self._repo.insert_document(doc)
