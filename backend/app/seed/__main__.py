"""CLI: validate and load the NOVA Mall seed.

Usage (from backend/, with DATABASE_URL set):

    python -m app.seed --validate-only
    python -m app.seed
    python -m app.seed --force
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.core.database import SessionLocal
from app.seed.nova_mall import build_nova_mall
from app.seed.validator import SeedValidationError, validate_seed
from app.services.seed_service import SeedAlreadyAppliedError, SeedService


async def _run(validate_only: bool, force: bool) -> int:
    doc = build_nova_mall()
    issues = validate_seed(doc)
    fatal = [i for i in issues if i.fatal]
    warnings = [i for i in issues if not i.fatal]
    for issue in warnings:
        print(f"warning [{issue.kind}] {issue.where}: {issue.message}", file=sys.stderr)
    if fatal:
        for issue in fatal:
            print(f"error [{issue.kind}] {issue.where}: {issue.message}", file=sys.stderr)
        return 1
    print(
        f"seed valid: {len(doc.floors)} floors, {len(doc.categories)} categories, "
        f"{len(doc.locations)} locations, {len(doc.nodes)} nodes, {len(doc.edges)} edges"
    )
    if validate_only:
        return 0

    async with SessionLocal() as session, session.begin():
        service = SeedService(session)
        try:
            mall = await service.apply(doc, force=force)
        except SeedAlreadyAppliedError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        except SeedValidationError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(f"seeded mall {mall.slug} id={mall.id}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and load the NOVA Mall seed")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Run the validator and print counts; do not touch the database",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an already-seeded mall with the same slug",
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_run(args.validate_only, args.force)))


if __name__ == "__main__":
    main()
