"""Tour algorithms on matrices. No database and no FastAPI."""

from __future__ import annotations

import math

from app.routing.tour import (
    brute_force_open,
    held_karp_open,
    nearest_neighbor,
    path_cost,
    solve_tour,
    two_opt,
    unreachable_from_start,
)

# Start 0, stops 1, 2, 3.
# NN takes the cheap first step into a trap (cost 102).
# Optimum is 0 → 2 → 3 → 1 (cost 4).
_TRAP = [
    [0, 1, 2, 10],
    [1, 0, 100, 100],
    [2, 1, 0, 1],
    [10, 1, 1, 0],
]


def test_nearest_neighbor_visits_each_stop_once_from_the_start() -> None:
    order = nearest_neighbor(_TRAP)
    assert order[0] == 0
    assert sorted(order) == [0, 1, 2, 3]
    assert path_cost(_TRAP, order) == 102


def test_nearest_neighbor_is_not_optimal() -> None:
    greedy = path_cost(_TRAP, nearest_neighbor(_TRAP))
    exact = path_cost(_TRAP, held_karp_open(_TRAP))
    assert greedy > exact
    assert exact == 4


def test_two_opt_never_worsens_and_keeps_every_stop() -> None:
    seed = nearest_neighbor(_TRAP)
    improved, moves = two_opt(_TRAP, seed)
    assert moves >= 1
    assert improved[0] == 0
    assert sorted(improved) == [0, 1, 2, 3]
    assert path_cost(_TRAP, improved) <= path_cost(_TRAP, seed)


def test_two_opt_leaves_an_optimal_tour_alone() -> None:
    optimal = held_karp_open(_TRAP)
    improved, moves = two_opt(_TRAP, optimal)
    assert moves == 0
    assert path_cost(_TRAP, improved) == path_cost(_TRAP, optimal)


def test_held_karp_matches_brute_force() -> None:
    matrices = [
        _TRAP,
        [
            [0, 5, 9, 4],
            [5, 0, 2, 8],
            [9, 2, 0, 3],
            [4, 8, 3, 0],
        ],
        [
            [0, 3, 8, 1, 7],
            [3, 0, 4, 6, 2],
            [8, 4, 0, 5, 9],
            [1, 6, 5, 0, 3],
            [7, 2, 9, 3, 0],
        ],
    ]
    for cost in matrices:
        exact = held_karp_open(cost)
        brute = brute_force_open(cost)
        assert path_cost(cost, exact) == path_cost(cost, brute)
        assert sorted(exact) == list(range(len(cost)))


def test_heuristic_is_at_least_the_exact_cost() -> None:
    solved = solve_tour(_TRAP, exact=True)
    assert solved is not None
    assert solved.algorithm == "held_karp"
    exact = path_cost(_TRAP, solved.exact_order or [])
    nn = path_cost(_TRAP, solved.nn_order)
    polished = path_cost(_TRAP, solved.nn_2opt_order)
    assert nn >= exact
    assert polished >= exact
    assert polished <= nn


def test_no_reshuffle_when_nothing_is_shorter() -> None:
    line = [
        [0, 1, 100],
        [100, 0, 1],
        [100, 100, 0],
    ]
    solved = solve_tour(line, exact=True)
    assert solved is not None
    assert path_cost(line, solved.order) == 2
    assert solved.order == [0, 1, 2]


def test_unreachable_stop_is_named() -> None:
    cost = [
        [0, 1, math.inf],
        [1, 0, math.inf],
        [math.inf, math.inf, 0],
    ]
    assert unreachable_from_start(cost) == [2]
    assert solve_tour(cost, exact=True) is None
