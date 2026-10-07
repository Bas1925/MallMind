"""Admissible heuristic for A*.

Same-floor: Euclidean distance in floor-local metres.
Cross-floor: the same 2D Euclidean distance (no extra vertical term).

Why that is admissible
----------------------
A heuristic h is admissible if h(n) ≤ true remaining cost. Euclidean
distance in the plane never overestimates walking distance along edges
whose lengths are at least the straight-line span (our seed authors
hallway/spur `distance_m` from coordinates). A vertical connector has
non-negative extra cost (elevator wait, stair length) on top of a
0-metre horizontal span, so ignoring it underestimates — still admissible.

Why we do not add a "must pay an elevator" bonus
------------------------------------------------
A lower bound of min(elevator wait) between different floors would still
be admissible *if every cross-floor path used an elevator*. Stairs can be
cheaper in time than an elevator wait on some seeds. A positive vertical
bonus could overestimate a stairs route. Zero extra is the safe choice.

Consistency: Euclidean satisfies the triangle inequality, and our edge
weights are ≥ coordinate span, so h(u) ≤ w(u,v) + h(v) on hallways.
Elevator edges at identical (x,y) have h(u)=h(v)=0 and w≥0.
"""

from __future__ import annotations

import math

from app.routing.constants import WALK_MPS
from app.routing.types import CostMode, GraphNode


def heuristic(current: GraphNode, goal: GraphNode, mode: CostMode) -> float:
    dx = current.x - goal.x
    dy = current.y - goal.y
    metres = math.hypot(dx, dy)
    if mode is CostMode.DISTANCE:
        return metres
    return metres / WALK_MPS
