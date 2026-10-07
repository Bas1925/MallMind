# 2026-10-06 — SVG y-flip vs viewBox origin

**Severity:** medium
**Time to find:** ~20 minutes (caught while wiring the floor rectangle, before E2E)
**Area:** map UI

## Symptom

Backend `y` increases north (ADR-007). SVG `y` increases down, so `toSvg` uses `bounds.maxY - y`. If `viewBox` still starts at `bounds.minY` (the unflipped south edge), the floor pad and the nodes live in different coordinate spaces: north stores sit in the padding, south stores sit on the clip edge.

## Hypothesis path

1. “Just flip y on each point” — enough for polylines, not for the outline `rect`.
2. “Put `transform=scale(1,-1)` on a group” — then every label has to be flipped back and hit-testing gets confusing.
3. After the flip, the mapped y-range is `[0, height]`, so the viewBox y-origin must be `0`, not `minY`.

## Root cause

Two coordinate systems were mixed in one SVG: original graph space for the outline, flipped space for markers and the route.

## Fix

`viewBox` and `floorRect` use `{ x: minX, y: 0, width, height }`. `toSvg` stays `{ x, y: maxY - y }`. Geometry tests lock north → y=0.

## Prevention

`src/lib/map-geometry.test.ts` asserts the flip and that `viewBox` starts at y=0.

## Lesson

A y-up domain model and a y-down renderer need one conversion at the boundary, including the camera (viewBox), not only the sprites.
