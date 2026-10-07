"""Measure open-tour solvers on NOVA Mall and on synthetic matrices.

    python scripts/bench_tour.py

Prints real timings and gaps. Does not write them into the docs by itself.
"""

from __future__ import annotations

import asyncio
import random
import time
import uuid

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Location
from app.repositories.graph_repository import GraphRepository
from app.routing.tour import held_karp_open, path_cost
from app.routing.types import CostMode, RouteProfile
from app.services.navigation import NavigationError
from app.services.tour_service import TourService

CANONICAL = ("main-entrance", ("nike", "zara", "apple", "atm-g", "super-pharm"))
SIZES = (3, 5, 7, 10, 12, 15, 20)
SAMPLES = 8


def _synthetic(k: int, rng: random.Random) -> list[list[float]]:
    n = k + 1
    cost = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                cost[i][j] = float(rng.randint(1, 100))
    return cost


def _time_held_karp() -> None:
    rng = random.Random(0)
    print("held-karp on random directed matrices (start + k stops)")
    for k in (3, 5, 7, 8, 10, 12, 14):
        cost = _synthetic(k, rng)
        import app.routing.tour as tour

        previous = tour.EXACT_MAX_STOPS
        tour.EXACT_MAX_STOPS = max(previous, k)
        t0 = time.perf_counter()
        order = held_karp_open(cost)
        elapsed = (time.perf_counter() - t0) * 1000
        tour.EXACT_MAX_STOPS = previous
        print(f"  k={k:2}  {elapsed:8.2f} ms  cost={path_cost(cost, order):.0f}")


async def _run() -> None:
    _time_held_karp()
    async with SessionLocal() as session:
        repo = GraphRepository(session)
        service = TourService(repo)
        rows = list((await session.scalars(select(Location))).all())
        by_slug = {row.slug: row.id for row in rows}
        start = by_slug["main-entrance"]
        others = [row.id for row in rows if row.slug != "main-entrance"]
        await _canonical(service, by_slug)
        rng = random.Random(0)
        print("\nNOVA samples, start=main-entrance, profile=normal, objective=distance")
        print(
            f"{'k':>3} {'n':>3} {'astar':>6} {'ms':>8} {'user':>8} {'nn':>8} "
            f"{'2opt':>8} {'exact':>8} {'nn%':>7} {'2opt%':>7}"
        )
        for k in SIZES:
            totals = []
            for _ in range(SAMPLES):
                stops = rng.sample(others, k)
                t0 = time.perf_counter()
                try:
                    plan = await service.plan(
                        start, stops, profile=RouteProfile.NORMAL, cost_mode=CostMode.DISTANCE
                    )
                except NavigationError as exc:
                    print(f"  k={k} failed {exc.code}: {exc.message}")
                    continue
                elapsed = (time.perf_counter() - t0) * 1000
                totals.append((elapsed, plan))
            if not totals:
                continue
            plans = [item[1] for item in totals]
            mean_ms = sum(item[0] for item in totals) / len(totals)
            mean_user = sum(item.original_distance_m for item in plans) / len(plans)
            mean_nn = sum(item.nearest_neighbor_distance_m for item in plans) / len(plans)
            mean_opt = sum(item.nearest_neighbor_2opt_distance_m for item in plans) / len(plans)
            exact_values = [
                item.exact_distance_m for item in plans if item.exact_distance_m is not None
            ]
            nn_gaps = [
                item.nearest_neighbor_gap_percent
                for item in plans
                if item.nearest_neighbor_gap_percent is not None
            ]
            opt_gaps = [
                item.nearest_neighbor_2opt_gap_percent
                for item in plans
                if item.nearest_neighbor_2opt_gap_percent is not None
            ]
            exact = "-" if not exact_values else f"{sum(exact_values) / len(exact_values):.0f}"
            nn_gap = "-" if not nn_gaps else f"{sum(nn_gaps) / len(nn_gaps):.1f}"
            opt_gap = "-" if not opt_gaps else f"{sum(opt_gaps) / len(opt_gaps):.1f}"
            print(
                f"{k:3} {len(plans):3} {plans[0].astar_calls:6} {mean_ms:8.1f} "
                f"{mean_user:8.0f} {mean_nn:8.0f} {mean_opt:8.0f} "
                f"{exact:>8} {nn_gap:>7} {opt_gap:>7}"
            )


async def _canonical(service: TourService, by_slug: dict[str, uuid.UUID]) -> None:
    start_slug, stops = CANONICAL
    plan = await service.plan(
        by_slug[start_slug],
        [by_slug[slug] for slug in stops],
        profile=RouteProfile.NORMAL,
        cost_mode=CostMode.DISTANCE,
    )
    print("\ncanonical main-entrance -> nike, zara, apple, atm-g, super-pharm")
    user_order = " -> ".join(stop.slug for stop in plan.original_order)
    print("  user   ", user_order, plan.original_distance_m)
    print(
        "  nn     ",
        plan.nearest_neighbor_distance_m,
        "gap",
        plan.nearest_neighbor_gap_percent,
    )
    print(
        "  2opt   ",
        plan.nearest_neighbor_2opt_distance_m,
        "gap",
        plan.nearest_neighbor_2opt_gap_percent,
        "moves",
        plan.two_opt_moves,
    )
    print("  exact  ", plan.exact_distance_m, plan.algorithm)
    print("  chosen ", " -> ".join(stop.slug for stop in plan.optimized_order))
    print(
        "  saved  ",
        plan.distance_saved_m,
        "m",
        plan.distance_saved_percent,
        "%",
        plan.estimated_time_saved_seconds,
        "s",
        "improved",
        plan.improved,
    )


if __name__ == "__main__":
    asyncio.run(_run())
