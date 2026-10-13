# MallMind: interview case study

## The problem

A shopping trip combines different questions: where is a place, how do I reach it without stairs, which order should I visit stores, and where did I park? MallMind combines those flows around one floor-local graph and a schematic, fictional mall.

## Technical story

The React/Next.js client renders an interactive SVG map and sends requests to FastAPI. Services retrieve graph and location data from PostgreSQL. A* computes point-to-point routes; Dijkstra provides an independent correctness baseline. Wheelchair and avoid-stairs profiles filter graph edges before routing.

Shopping trips compute directed A* costs between stops. Held–Karp finds the exact open-tour order for up to 12 stops; larger trips use nearest-neighbor plus directed 2-opt. This cutoff makes the quality/runtime tradeoff explicit.

The search layer combines lexical matching and optional semantic embeddings behind a provider interface. The assistant uses retrieved places and routing tools; multilingual templates work without a paid chat model. Optional model integration is implemented but is not verified as a live hosted feature.

## Evidence

Re-measured on 13 October 2026 using the current seeded NOVA graph: 3 floors, 33 locations, 110 nodes and 288 directed edges. The two additional locations belong to the BFS/DFS service-maze example.

| Experiment | Result | Boundary |
|---|---|---|
| Main Entrance → MUJI | A*: 27 nodes expanded; Dijkstra: 71; equal 118 m route cost | 62.0% fewer expansions on this specific route |
| Five-stop shopping trip | 442.5 m → 382.5 m; 60 m / 13.6% saved | Seeded example, not a measured customer outcome |
| 100×100 synthetic grid | Both expand 10,000 nodes | A* is not universally faster |

The earlier 20-stop timing is retained only in the historical release review; it was not re-measured on the updated seed for this publication pass.

Reproduce using `backend/scripts/bench_routing.py` and `backend/scripts/bench_tour.py`. The five stops are Nike, Zara, Apple, ATM Ground, and Super-Pharm, starting at Main Entrance. Timing varies with hardware and system load.

## Reliability improvements

Changing a route endpoint now cancels the pending request and clears the displayed route. Late search results cannot repopulate a cleared query. Editing a shopping list invalidates its previous plan, and leaving the assistant prevents a late reply from changing the map. Tests exercise these user-visible failures, including delayed responses.

Keyboard search supports arrow keys, Enter, Escape, and announced selection. The UI supports keyboard map selection, reduced motion, explicit error recovery, and small-screen layouts. These are implemented accessibility features, not a claim of complete WCAG conformance.

## Two-minute demonstration

Begin on the store directory: filter by category/floor, open a store detail, and add stores to My visit. The same selection feeds the existing planner; changing the list invalidates an outdated plan. The map remains a separate view, with browser Back returning to the filtered directory.

1. Search for Nike using the keyboard; select it and set a route from Main Entrance.
2. Choose Apple and Wheelchair, then switch to Level 1 to show the next segment.
3. Add the five benchmark stops in Plan; show the distance saved and explain exact vs heuristic ordering.
4. Ask about Nike in Arabic, then ask about an unknown store to show the grounded fallback.
5. Save parking details, refresh, and explain that the information stays on the device.

## CV wording

The standalone, copy-ready version is in [cv-project-entry.md](cv-project-entry.md). It describes a synthetic prototype, not a deployed mall product.

**MallMind — Indoor Navigation & Shopping Trip Planner**

Next.js · TypeScript · FastAPI · PostgreSQL · pgvector

- Built a full-stack indoor navigation application with accessible A* routing, interactive multi-floor maps, multilingual search, and device-local parking memory.
- Implemented exact and heuristic multi-stop optimization, reducing distance by 13.6% on a reproducible five-stop demo; compared A* with Dijkstra for correctness and search effort.
- Added automated component, integration, and desktop/mobile browser tests, plus container deployment configuration and CI workflows.

Describe only the work and decisions you can explain confidently. Add GitHub and live-demo links once published. Avoid claiming real indoor positioning, surveyed maps, real users, production uptime, or live model verification without evidence.

## Questions to prepare for

- Why use a graph instead of calculating straight-line distances?
- How do directed escalators and wheelchair constraints change reachability?
- Why can A* expand as many nodes as Dijkstra?
- Why switch away from exact tour optimization after 12 stops?
- What happens if requests finish out of order?
- What is the difference between lexical search, semantic search, and generated answers?
- What changes before supporting real malls, location sensors, or account synchronization?

The next product evidence would be usability sessions with a few people unfamiliar with the app: record whether they finish the five demo tasks, where they hesitate, and what changes improve completion. No user-study results are claimed here.
