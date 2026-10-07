"""Open shopping tours on a cost matrix.

A* answers one pair. This module only orders the visits. Index 0 is the
fixed start. The tour does not return to the start: a shopper finishes at
the last store.

Held-Karp is the exact solver. Nearest Neighbor + 2-opt is the heuristic.
Neither file imports FastAPI.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise

INF = math.inf
# A tour must be shorter by more than a centimetre to count as an improvement.
EPS = 1e-2

# Held-Karp is O(2^k * k^2). bench_tour.py on 2026-10-06, CPython 3.12,
# random directed matrices: k=10 17 ms, k=12 89 ms, k=14 543 ms.
# 12 stays inside one request. 14 does not. The guard also stops a
# caller from building a 2^20 table.
EXACT_MAX_STOPS = 12


@dataclass(frozen=True)
class SolvedTour:
    order: list[int]
    algorithm: str
    nn_order: list[int]
    nn_2opt_order: list[int]
    exact_order: list[int] | None
    two_opt_moves: int


def path_cost(cost: list[list[float]], order: list[int]) -> float:
    total = 0.0
    for left, right in pairwise(order):
        step = cost[left][right]
        if math.isinf(step):
            return INF
        total += step
    return total


def nearest_neighbor(cost: list[list[float]]) -> list[int]:
    """Greedy open tour. O(k^2) on the matrix. Not optimal.

    Ties take the lowest index so the same matrix always yields the same tour.
    """
    n = len(cost)
    visited = {0}
    order = [0]
    while len(order) < n:
        current = order[-1]
        choice = -1
        best = INF
        for nxt in range(n):
            if nxt in visited:
                continue
            step = cost[current][nxt]
            if step < best:
                best = step
                choice = nxt
        if choice < 0 or math.isinf(best):
            break
        visited.add(choice)
        order.append(choice)
    return order


def two_opt(cost: list[list[float]], order: list[int]) -> tuple[list[int], int]:
    """Reverse segments of an open path while the cost falls.

    The start stays at index 0. Each accepted move is strictly cheaper, so
    the result is never worse than the input. It is a local optimum of the
    2-opt neighbourhood, not a global one.
    """
    route = list(order)
    moves = 0
    while True:
        best_delta = 0.0
        best_span: tuple[int, int] | None = None
        n = len(route)
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                delta = _reversal_delta(cost, route, i, j)
                if delta < best_delta - 1e-9:
                    best_delta = delta
                    best_span = (i, j)
        if best_span is None:
            return route, moves
        i, j = best_span
        route[i : j + 1] = reversed(route[i : j + 1])
        moves += 1
        if moves > n * n:
            return route, moves


def held_karp_open(cost: list[list[float]]) -> list[int]:
    """Exact open tour. Start is fixed. The end is whichever stop is cheapest.

    State dp[mask][j]: cheapest way to visit the stops in `mask`, ending at
    stop j. Stops are numbered 0..k-1 in the mask and stored as matrix
    indexes 1..k.

    Recurrence: dp[mask][j] = min over i in mask, i != j, of
        dp[mask without j][i] + cost[i][j]
    Base: dp[{j}][j] = cost[start][j]

    Time O(2^k * k^2), space O(2^k * k). k is the number of stops, not
    counting the start.
    """
    n = len(cost)
    k = n - 1
    if k <= 0:
        return [0]
    if k == 1:
        if math.isinf(cost[0][1]):
            return []
        return [0, 1]
    if k > EXACT_MAX_STOPS:
        raise ValueError(f"held_karp_open refuses k={k}; cutoff is {EXACT_MAX_STOPS}")

    full = (1 << k) - 1
    dp = [[INF] * k for _ in range(1 << k)]
    parent = [[-1] * k for _ in range(1 << k)]
    for j in range(k):
        dp[1 << j][j] = cost[0][j + 1]

    for mask in range(1 << k):
        for j in range(k):
            if (mask & (1 << j)) == 0 or math.isinf(dp[mask][j]):
                continue
            for nxt in range(k):
                if mask & (1 << nxt):
                    continue
                step = cost[j + 1][nxt + 1]
                if math.isinf(step):
                    continue
                cand = dp[mask][j] + step
                bit = mask | (1 << nxt)
                if cand < dp[bit][nxt]:
                    dp[bit][nxt] = cand
                    parent[bit][nxt] = j

    end = min(range(k), key=lambda j: dp[full][j])
    if math.isinf(dp[full][end]):
        return []

    rev: list[int] = []
    mask = full
    j = end
    while j != -1:
        rev.append(j + 1)
        prev = parent[mask][j]
        mask ^= 1 << j
        j = prev
    rev.append(0)
    rev.reverse()
    return rev


def brute_force_open(cost: list[list[float]]) -> list[int]:
    """Every permutation of the stops. For tests, and only for tiny k."""
    from itertools import permutations

    n = len(cost)
    stops = list(range(1, n))
    best_order: list[int] = []
    best = INF
    for perm in permutations(stops):
        order = [0, *perm]
        total = path_cost(cost, order)
        if total < best:
            best = total
            best_order = order
    return best_order


def unreachable_from_start(cost: list[list[float]]) -> list[int]:
    """Stops with no finite directed path from the start, via other stops."""
    n = len(cost)
    seen = {0}
    stack = [0]
    while stack:
        current = stack.pop()
        for nxt in range(n):
            if nxt in seen or math.isinf(cost[current][nxt]):
                continue
            seen.add(nxt)
            stack.append(nxt)
    return [index for index in range(1, n) if index not in seen]


def solve_tour(cost: list[list[float]], *, exact: bool) -> SolvedTour | None:
    """Best open tour we are willing to compute.

    Exact, when requested, wins on cost. A tie with the user order is still
    reported as held_karp: we proved that order is optimal. The heuristic is
    kept only when it is strictly cheaper than the submitted order and exact
    did not run. A heuristic that is not cheaper than the submitted order is
    discarded so we do not reshuffle a shopper for zero gain.
    """
    n = len(cost)
    user = list(range(n))
    nn = nearest_neighbor(cost)
    improved, moves = two_opt(cost, nn)
    exact_order = held_karp_open(cost) if exact else None

    chosen = user
    algorithm = "user_order"
    if _complete(cost, improved) and path_cost(cost, improved) < path_cost(cost, chosen) - EPS:
        chosen = improved
        algorithm = "nearest_neighbor_2opt"
    if exact_order is not None and _complete(cost, exact_order):
        exact_cost = path_cost(cost, exact_order)
        chosen_cost = path_cost(cost, chosen)
        if exact_cost <= chosen_cost + EPS:
            chosen = exact_order
            algorithm = "held_karp"
    if not _complete(cost, chosen):
        return None
    return SolvedTour(
        order=chosen,
        algorithm=algorithm,
        nn_order=nn,
        nn_2opt_order=improved,
        exact_order=exact_order,
        two_opt_moves=moves,
    )


def _complete(cost: list[list[float]], order: list[int]) -> bool:
    return (
        len(order) == len(cost)
        and len(set(order)) == len(cost)
        and not math.isinf(path_cost(cost, order))
    )


def _reversal_delta(cost: list[list[float]], route: list[int], i: int, j: int) -> float:
    """Cost change from reversing route[i:j+1].

    On a symmetric matrix only the two boundary edges change. Mall edges are
    directed (an up escalator is not a down escalator), so the reversed
    segment's internal edges are repriced too.
    """
    old = cost[route[i - 1]][route[i]]
    new = cost[route[i - 1]][route[j]]
    for left in range(i, j):
        old += cost[route[left]][route[left + 1]]
        new += cost[route[left + 1]][route[left]]
    if j + 1 < len(route):
        old += cost[route[j]][route[j + 1]]
        new += cost[route[i]][route[j + 1]]
    if math.isinf(new):
        return INF
    if math.isinf(old):
        return -INF
    return new - old
