# 04 — Phase 3: Interactive mall map + navigation UI

**Status:** Complete against portable PostgreSQL 16.15. Lint, typecheck, production build, 13 Vitest tests, and 1 Playwright route E2E against the live A* API all passed. Phase 4 continued from here.
**Date:** 2026-10-06.

The frontend is a presentation layer over Phase 1 coordinates and Phase 2 A*. It is not a second map.

---

## 1. Why SVG

See [ADR-010](decisions/010-svg-for-indoor-map-rendering.md).

Canvas and WebGL were rejected: the graph is 91 nodes / 248 edges. We need clickable stores, floor tabs, an inspectable route path, and a debug overlay that shows the same vertices A* expands. SVG is the cheapest way to get all of that.

Coordinate rule (same as ADR-007):

- Backend: origin south-west, `x` east, `y` north.
- SVG: `y` down, so `toSvg(x, y) = { x, y: bounds.maxY - y }`.
- `viewBox` y-origin is `0` after that flip so the floor rectangle and the nodes share one space.

---

## 2. Backend / frontend data flow

```
GET  /api/v1/malls/nova-mall/map
        → mall, floors, locations, nodes, edges
        → drawn as SVG (one payload; NOVA is small)

User picks from / to / profile
        → POST /api/v1/navigation/route
        → FastAPI → NavigationService → A*
        → { node_ids, distance_m, estimated_seconds, floors, instructions, … }

Frontend joins node_ids to map.nodes coordinates
        → RouteLayer draws the active floor's segment
```

There is no client-side pathfinding.

### Map API shape

`GET /api/v1/malls/{slug}/map` returns one document:

| Field | Why the UI needs it |
|---|---|
| `mall` | title |
| `floors` | floor selector |
| `locations` | markers, search, from/to dropdowns |
| `nodes` | coordinates + debug graph |
| `edges` | hallway strokes + debug arrows + vertical hop type |

One GET rather than per-floor: three floors, 91 nodes. Caching the static payload in React state is enough. We do not refetch on floor change.

`GET /api/v1/malls/{slug}/locations?q=` exists for ILIKE (+ bathroom→restroom aliases). The search box filters the already-loaded map on each keystroke so typing does not hammer the API. Both use the same backend rows.

Types are hand-written in `frontend/src/types/`. OpenAPI codegen was deferred: two read models, adding `openapi-typescript` plus a generate step is more CI surface than drift risk today. The risk is a silent field rename; the map API tests lock counts and Nike's coordinates.

---

## 3. Frontend architecture

```
src/
  app/page.tsx                 # mounts MallExplorer
  components/
    MallExplorer.tsx           # local state; loads map; posts routes
    map/
      MallMap.tsx              # SVG document: outline, hallways, layers
      FloorSelector.tsx
      RouteLayer.tsx           # A* polyline + vertical markers
      LocationMarker.tsx
      GraphDebugLayer.tsx      # off by default
    navigation/
      RouteForm.tsx
      RouteSummary.tsx
      RouteInstructions.tsx    # Phase 2 strings, no LLM
      LocationCard.tsx
    search/
      LocationSearch.tsx       # client filter of loaded locations
  lib/
    api.ts                     # fetchMallMap, requestRoute
    map-geometry.ts            # y-flip, bounds, routeOnFloor
    location-search.ts
    errors.ts
  types/
    map.ts
    navigation.ts              # re-exports route types
```

`lib/` instead of `services/`: these are fetch helpers, not a domain layer.

### Component responsibilities

| Component | Owns |
|---|---|
| `MallExplorer` | load/error, selection, profile, route request |
| `MallMap` | SVG composition for the active floor |
| `RouteLayer` | path from backend node ids |
| `GraphDebugLayer` | nodes, directed hallway edges, short ids |
| `RouteForm` | from / to / profile / submit |
| `LocationSearch` | query string (keeps keystrokes off the map tree) |

---

## 4. State management

**Local React state in `MallExplorer`.** No Redux, Zustand, or Context.

The live state is: which floor, which two location ids, which profile, the last `RouteResponse`, whether the debug overlay is on. That is one screen. URL state can be added later for shareable `?from=&to=` links; it is not required to demo routing.

Search query lives inside `LocationSearch` so typing does not re-render the SVG.

---

## 5. Route rendering

1. `route.node_ids` (fallback: `route.route`) are graph vertex ids from A*.
2. `routeOnFloor` walks consecutive pairs, emits polylines whose nodes have `floor_level === active`, and records elevator/stairs/escalator hops when the floor changes.
3. Other floors keep the route object; only the active segment is stroked.
4. Banner: “Continue via elevator to Level 1” (or arrived-from).

Internal vertices stay hidden unless **Show graph** is on.

---

## 6. Accessibility UI

Profiles `normal` | `wheelchair` | `avoid_stairs` are sent as `profile` on `POST /navigation/route`. Changing the radio while origin and destination are set re-requests. Wheelchair uses the same A* with `edge.accessible`; if the backend returns `no_accessible_path`, the panel shows a specific error — not a blank map.

---

## 7. RTL foundation

No translations in this phase. Layout uses logical properties (`start` / `end` / `ms-` / `border-s`) and `text-start`. Do not add `flex-row-reverse` for “visual polish.”

---

## 8. Testing

- Vitest + Testing Library: request body, wheelchair profile, no-route error, floor tab, segment change, search focus.
- Playwright `e2e/navigation.spec.ts`: real `GET /map` + `POST /navigation/route` against the seeded API. Fail if `:8000` is down. Do not skip.

---

## 9. Source of truth

Backend/domain owns locations, graph, route, floors. Frontend owns presentation and interaction state only. If the SVG ever disagrees with `POST /navigation/route`, the SVG is wrong.
