# 010 — SVG for indoor map rendering

**Status:** Accepted
**Date:** 2026-10-06
**Deciders:** Basel

## Context

Phase 3 needs an interactive NOVA Mall map: clickable locations, floor switching, a real A* polyline, optional graph debug, and a usable mobile layout. The routing graph already stores floor-local `(x, y)` (ADR-007). The frontend must not invent a second map.

## Options considered

### Option A — SVG
- **Pros:** nodes and edges map 1:1 to DOM; routes are `<path>`; stores are focusable; screen readers get titles; inspecting a route in DevTools is trivial; the graph is tiny (91 nodes).
- **Cons:** thousands of DOM nodes would hurt. We do not have thousands.

### Option B — HTML Canvas
- **Pros:** cheap to redraw many primitives.
- **Cons:** hit-testing, a11y, and debugging all become custom code. A recruiter cannot inspect a canvas pixel and see `node-id`.

### Option C — WebGL / MapLibre / deck.gl
- **Pros:** real GIS stacks, GPU pan/zoom.
- **Cons:** indoor schematic is not GIS. We would fight tile coordinates for a 120×90 metre plan. Interview value is the algorithm, not the map engine.

## Decision

**Option A.** Render each floor as one SVG `viewBox` derived from that floor's graph bounds. Backend `y` increases north; SVG `y` increases down, so the renderer flips `y` at the boundary. Pan/zoom is CSS scaling of the viewBox, not a mapping library.

## Why

The product requirement is “show the path A* actually returned.” SVG lets the route layer join `route.node_ids` to `map.nodes[].(x,y)` with no extra model. Accessibility and debug mode (node ids on the same coordinates the heap searched) fall out of the DOM.

## Trade-offs

- We will outgrow SVG if a later mall has tens of thousands of rendered labels. Then we hide labels by default (already done) or move the debug layer to canvas. The user-facing route stays SVG until measurement says otherwise.
- We do not get Mapbox-style vector tiles. We do not need them.

## What would change this later

- A floor with > ~2k always-visible labels and jank on mid-range phones.
- A requirement to overlay the indoor plan on outdoor OSM.

Until then, SVG is the simplest technology that hits click, floor switch, route draw, a11y, and debug.
