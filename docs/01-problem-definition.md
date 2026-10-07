# 01 — Problem Definition

**Status:** Approved, 2026-10-05.
**Owner:** Basel.
**Reviewed by:** —

This document is the contract between "what we're building" and "what we're not." Everything downstream (ADRs, DB schema, API, tests) should trace back to a requirement listed here. If a feature doesn't trace back, it's scope creep and we drop it or amend this doc with an explicit decision.

---

## 1. Problem statement

> Visitors to large shopping malls cannot efficiently find stores, facilities, and accessible routes, and cannot ask natural-language questions about the mall. Existing solutions (printed boards, mall websites, Google Maps) stop at the mall's front door or fail users with accessibility needs or language barriers.

## 2. Who we're building for (personas)

We'll keep this small — four personas, each driving at least one feature.

### P1. Fatima — First-time visitor, Arabic speaker
- 28, visiting the mall for the first time
- Reads Arabic, limited English
- Wants to find a specific store and a bathroom
- Pain: no idea where anything is; signs are in Hebrew/English only

### P2. Yossi — Regular shopper, local
- 45, visits the mall weekly
- Reads Hebrew and English
- Pain: forgets where he parked in a 3-level underground lot

### P3. Dan — Wheelchair user
- 34, mobility-impaired
- Needs routes that use elevators, never stairs
- Pain: existing map apps don't flag inaccessible routes

### P4. Emma — Tourist with a shopping list
- 29, in the country for a week
- English only, has a list of 4 brands to visit
- Pain: walks a km of unnecessary backtracking

Non-targets: mall operators (we don't build an admin console in MVP), store owners (we don't integrate with POS systems).

## 3. User stories

Format: *As a <persona>, I want <action>, so that <benefit>.*

| # | Story | Persona | MVP? |
|---|---|---|---|
| US-01 | Search for a store by name | P1, P4 | ✅ |
| US-02 | Get walking directions from a chosen start to a chosen destination | All | ✅ |
| US-03 | See distance, walking time, and floor changes in the route | All | ✅ |
| US-04 | Choose an "accessible" route that avoids stairs | P3 | ✅ |
| US-05 | Ask natural-language questions about the mall in my language | P1, P4 | ✅ |
| US-06 | Receive "I don't know" when the system has no reliable answer | All | ✅ |
| US-07 | Search by intent ("somewhere to buy running shoes") | P4 | ✅ |
| US-08 | Save multiple stores and get an optimized visit order | P4 | Phase 2 |
| US-09 | Save my parking location and look it up later | P2 | Phase 2 |
| US-10 | Create an account and persist my preferences | P2 | Phase 2 |

## 4. Functional requirements

Numbered, atomic, testable.

| # | Requirement |
|---|---|
| FR-01 | The system shall return the shortest walkable path between any two reachable nodes in the mall graph. |
| FR-02 | The system shall support a navigation mode that excludes stairs and escalators (`accessible`). |
| FR-03 | The system shall return turn-by-turn directions including: per-step distance in meters, floor, and edge type. |
| FR-04 | The system shall indicate every floor change in the returned route. |
| FR-05 | The system shall report "no route found" (not raise an unhandled error) when the graph is disconnected for the requested mode. |
| FR-06 | The system shall accept text queries in English, Arabic, and Hebrew. |
| FR-07 | The system shall provide search results ranked by relevance, combining substring text match and semantic similarity. |
| FR-08 | The AI assistant shall refuse to answer when retrieved context is empty or below a configured confidence threshold. |
| FR-09 | The AI assistant shall cite the source location(s) used to answer a factual question. |
| FR-10 | The system shall accept a list of up to 10 destinations and return a visit order that is no longer than the user's original order (Phase 2). |
| FR-11 | Authenticated users shall be able to create, read, update, and delete their current parking location (Phase 2). |

## 5. Non-functional requirements

| # | Category | Requirement | How we'll verify |
|---|---|---|---|
| NFR-01 | Performance | Route endpoint P95 < 100 ms on dev laptop for a 2k-node graph | Load script + logs |
| NFR-02 | Performance | Search endpoint P95 < 300 ms | Load script + logs |
| NFR-03 | Performance | AI assistant endpoint P95 < 3 s | Logs (LLM-bound) |
| NFR-04 | Security | Passwords stored as bcrypt hashes (cost ≥ 12) | Code review + test |
| NFR-05 | Security | All inputs validated via Pydantic schemas at router boundary | Code review |
| NFR-06 | Security | No raw string concatenation in SQL; parameterized queries only | Static check + review |
| NFR-07 | Security | Secrets provided via environment variables; `.env` never committed | `.gitignore` + CI check |
| NFR-08 | Reliability | Every unhandled exception produces a structured log with a correlation ID | Middleware + log inspection |
| NFR-09 | Reliability | Health endpoint returns 200 only when DB connectivity is good | Integration test |
| NFR-10 | Observability | All API requests logged as JSON with method, path, status, duration | Middleware |
| NFR-11 | Testability | Algorithm modules have ≥ 80% line coverage; backend overall ≥ 60% | `pytest --cov` in CI |
| NFR-12 | Portability | Full stack runs locally with `docker compose up` | Manual + CI |
| NFR-13 | Accessibility | Frontend WCAG 2.1 AA on primary flows; keyboard navigable | Lighthouse + manual |
| NFR-14 | i18n | UI renders correctly in English, Hebrew (RTL), Arabic (RTL) | Visual + Playwright |

## 6. MVP scope

**In scope** (shipped end of Phase 8):

- Indoor navigation (A*, Dijkstra available) — US-02, US-03, FR-01, FR-03, FR-04, FR-05
- Accessible routing mode — US-04, FR-02
- Hybrid search — US-01, US-07, FR-07
- AI assistant with RAG grounding — US-05, US-06, FR-06, FR-08, FR-09
- One hardcoded demo mall (adapted from the HTML prototype)
- Dockerized local dev; CI runs tests and lint on push
- Deployed demo URL

**Not in MVP** (Phase 2 or later):

- Multi-stop tour optimization (nearest-neighbor TSP)
- Parking memory
- User accounts and favorites

## 7. Things we are intentionally NOT building

Listed explicitly so scope creep gets caught in code review.

| Not building | Why |
|---|---|
| Real indoor positioning (BLE / UWB beacons) | Requires physical hardware and is a whole industry. We assume the user picks their start on the map. |
| Store POS / inventory integration | Needs business partnerships; outside our control. |
| Real-time crowd / wait-time data | Needs sensors or scraping; brittle and non-core. |
| Native mobile apps | Mobile-first web covers 100% of the user story. |
| Multi-mall tenancy / admin console | We seed one mall. Multi-tenancy is a different product. |
| Payments, loyalty, offers, push notifications | Outside the core "find things" problem. |
| Social features (friends, shared lists) | Not needed to demonstrate engineering depth. |
| OCR / computer-vision parking spot detection | Fun but orthogonal; parking will be a plain text form. |

## 8. Technical risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-01 | LLM hallucinates despite RAG | Medium | High (safety / trust) | Strict grounding prompt + refusal tests; cite sources |
| R-02 | A* with time-cost edges and a distance-based heuristic becomes inadmissible → suboptimal routes | Low | Medium | Keep heuristic in meters; convert to time only in the cost; add Dijkstra cross-check in tests |
| R-03 | pgvector too slow at scale | Low (for MVP) | Low | Not an MVP concern; measure before worrying. Switch to HNSW if needed |
| R-04 | LLM provider cost or rate limits block demo | Medium | Medium | Wrap behind interface; cache responses; Groq free tier as fallback |
| R-05 | In-memory graph goes stale after a map edit | Low | Low | `POST /admin/graph/reload` + graph version header |
| R-06 | Seed data integrity (one-way edges, mismatched floors) | High | Medium | Seed script runs validation (bidirectional check unless intentional, floor sanity) |
| R-07 | Multi-floor route gives nonsensical directions due to coordinate inconsistency | Medium | Medium | Unit test fixtures with known multi-floor paths; manual visual inspection in Phase 3 |
| R-08 | Multilingual search quality for Hebrew/Arabic in semantic mode | Medium | Medium | Use a multilingual embedding model; add language-tagged test queries |

## 9. Assumptions

| # | Assumption | If wrong, we… |
|---|---|---|
| A-01 | The mall layout is static enough to hand-curate the graph | …need an admin tool (big scope expansion) |
| A-02 | Users can specify their start location (click on map or pick from list) | …need indoor positioning (out of scope) |
| A-03 | One demo mall is sufficient to demonstrate the engineering | …add a mall-switching UI in Phase 2 |
| A-04 | Internet is available for LLM calls | …show a graceful "assistant unavailable" state |
| A-05 | Mall graph fits comfortably in RAM (< 50 MB for the demo mall) | …swap in a persistent graph store (unlikely at this scale) |
| A-06 | We don't need rate limiting for a portfolio demo | …add a token-bucket middleware |
| A-07 | A single-region deployment is acceptable | …add CDN + multi-region (out of scope) |

## 10. Success criteria

Measurable. Each one is a thing we can show, run, or point at.

| # | Criterion | How to measure |
|---|---|---|
| SC-01 | Can demo the four MVP features end-to-end in < 5 minutes | Timed walkthrough |
| SC-02 | A* unit tests cover: happy path, no-path, same-node, accessible mode — all green | `pytest -k astar` |
| SC-03 | A* and Dijkstra agree on test fixtures (correctness cross-check) | Property-based test |
| SC-04 | Backend tests run in < 30 s locally; CI pipeline < 5 min total | CI output |
| SC-05 | Route endpoint P95 < 100 ms on dev laptop | Benchmark script committed to repo |
| SC-06 | README explains every top-10 engineering decision with a link to its ADR | Review |
| SC-07 | Three Playwright E2E flows green: search → details, navigate A→B, assistant Q&A | `npm run test:e2e` |
| SC-08 | Zero `any` in frontend `src/` (CI enforced) | `eslint --max-warnings=0` with `@typescript-eslint/no-explicit-any` |
| SC-09 | At least 4 ADRs written before beta demo (currently 3) | File count under `docs/decisions/` |
| SC-10 | At least one real debugging story in `docs/debugging/` | File count |
| SC-11 | Public demo URL loads in < 3 s on 4G | WebPageTest / Lighthouse |
| SC-12 | Assistant refuses (not hallucinates) on an unknown-store question in all three languages | Automated test |

## 11. Out of scope for this document

- The exact DB schema → covered in Phase 1 planning.
- The precise cost function for A* → covered in Phase 2 planning.
- The RAG prompt template → covered in Phase 5 planning.

Those get their own smaller planning docs when we reach each phase.
