# 007 — Floor-local Cartesian coordinates for graph nodes

**Status:** Accepted
**Date:** 2026-10-06
**Deciders:** Basel

## Context

Every `map_nodes` row needs a position so that:

- A* (Phase 2) can use Euclidean distance as an admissible heuristic
- the map UI (Phase 3) can draw nodes and routes on an SVG floor plan

We have to pick a coordinate system now, because the seed data stores numbers that A* will later treat as metric.

## Options considered

### Option A — Geographic lat/lng (WGS84)
- **Pros:** interoperable with outdoor maps.
- **Cons:** malls are indoors; GPS error is tens of metres; two floors share the same lat/lng; distances need haversine; overkill.

### Option B — A single 3D coordinate `(x, y, z)` in metres from a mall origin
- **Pros:** one space for the whole building; vertical distance is a real number.
- **Cons:** A*'s Euclidean heuristic in 3D *underestimates* walking cost through an elevator (you cannot walk through the floor slab), so it stays admissible but becomes looser. Floor plans are 2D drawings; authors think in per-floor pixels. Mixing z into the seed is extra cognitive load for no Phase-1 gain.

### Option C — Floor-local 2D Cartesian `(x, y)` in abstract metres, plus `floor_id`
- **Pros:** matches how floor plans are drawn; heuristic on the same floor is exactly Euclidean and tight; between floors the heuristic is still admissible if we ignore the vertical wait (it underestimates). Seed authors place a store by looking at a floor image.
- **Cons:** the same `(x, y)` on two floors is *not* the same point in 3D — we rely on `floor_id` to disambiguate. Vertical connectors must be authored with matching `(x, y)` so they "stack" visually.

## Decision

**Option C.** `map_nodes.x` and `map_nodes.y` are `DOUBLE PRECISION`, floor-local, in metres-like units, origin at the south-west corner of that floor's plan, x increasing east, y increasing north. Vertical connectors (elevator, stairs, escalators) are authored at the **same `(x, y)` on every floor they serve**.

They are "metres-like" rather than surveyed metres: the seed is a schematic. Distances on edges are authored separately (`distance_m`) and are the ground truth for path cost. Coordinates exist for the heuristic and the drawing; they do not have to match `distance_m` to the millimetre.

## Why

1. **Heuristic quality.** Same-floor Euclidean distance is a tight admissible heuristic. That is the whole point of preferring A* over Dijkstra.
2. **Authored like a floor plan.** One 2D drawing per floor is how mall maps actually exist.
3. **Vertical stacking is a convention, not a computed join.** Matching `(x, y)` across floors is a seed-validator check for elevator/stairs landings, not a DB constraint (it would require a self-join).

## Trade-offs

| We give up | We accept this because |
|---|---|
| True 3D distances | Walking through a slab is illegal; 3D Euclidean would lie in a different direction. |
| Pixel coordinates from a specific SVG | Metres-like units stay stable if we replace the drawing. |
| GIS interoperability | Indoor routing does not need it. |

## What would change this later

- A real CAD / BIM import that already has a building-origin 3D frame — we would store both the local 2D (for drawing) and a 3D point (for import round-trip).
- Indoor positioning (BLE) that reports a building-frame coordinate — then we add a transform from building-frame to floor-local.
