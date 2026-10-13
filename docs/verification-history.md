# Historical project notes

Archived from the pre-review README on 12 October 2026. Historical CI assertions below were not independently confirmed in this review; see release-review.md for current evidence. Screenshot files may since have been refreshed.

# MallMind — AI-Powered Mall Navigation Platform

Indoor navigation, hybrid search, and a RAG-grounded AI assistant for large shopping malls.

![MallMind: light visitor guide with a dimensional interactive floor map](screenshots/overview.jpg)

The visitor guide now uses a mint, forest-green, peach, and lilac palette; a switchable 2D/dimensional map; floor transitions; and responsive route, trip-planning, concierge, and parking panels. Motion respects reduced-motion preferences. The map is a schematic wayfinding view, not surveyed architectural geometry.

The overview above was captured from the running production build. Earlier feature captures remain in `docs/screenshots/`.

> **Status:** Phase 6 device-local parking memory is implemented. Shopping-tour pair costs still come from A*. Account sync and live chat-model verification are pending. Docker engine remains blocked locally (VMP).

## What this is

MallMind is a mobile-first web application that helps people find stores, bathrooms, elevators, and exits inside a large mall, plan efficient multi-store shopping trips, and ask questions in English, Hebrew, or Arabic — without requiring any integration with individual stores.

Engineering focus:

- **Graph-based indoor routing** using A* (with Dijkstra as a cross-check baseline)
- **Accessible routing** (wheelchair / no-stairs mode)
- **Hybrid search** combining SQL text search with semantic vector search
- **RAG-grounded AI assistant** that refuses to hallucinate when it has no evidence
- **Privacy-first parking memory** stored on the visitor's device, with a route back to the mapped entrance

## Tech stack

| Layer | Choice | Why / ADR |
|---|---|---|
| Frontend | Next.js 15 + React 19 + TypeScript (strict) + Tailwind | Strict typing enforced; zero `any` in `src/` |
| Backend | FastAPI (Python 3.12) | [ADR-004](decisions/004-use-fastapi.md) |
| Database | PostgreSQL 16 + `pgvector` + `pg_trgm` | [ADR-003](decisions/003-postgresql-with-pgvector.md) |
| Architecture | Modular monolith | [ADR-001](decisions/001-modular-monolith.md) |
| Routing | A* in production, Dijkstra as baseline | [ADR-002](decisions/002-astar-with-dijkstra-baseline.md) |
| Dev | Docker Compose | 3 services, hot reload for both backend and frontend |
| CI | GitHub Actions | Lint + tests + typecheck + build on every push |

## Quick start

Prerequisites: Docker Desktop (or any Docker + Compose v2 install).

```bash
# From the mallmind/ directory
cp .env.example .env
docker compose up --build
```

Then open:

- Frontend : <http://localhost:3000>
- Backend  : <http://localhost:8000/api/v1/health>
- API docs : <http://localhost:8000/docs>

The frontend home page is the NOVA Mall map. Pick origin and destination, then **Show route** — the path is `POST /api/v1/navigation/route`, not a client-side fake.

## Running outside Docker

Backend (needs a Postgres you point at via `DATABASE_URL`):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev-lock.txt            # deterministic install
pip install -e . --no-deps                          # make the app importable
set DATABASE_URL=postgresql+asyncpg://mallmind:mallmind_dev_only@127.0.0.1:5432/mallmind
alembic upgrade head
python -m app.seed --force
uvicorn app.main:app --reload
```

On this machine that URL talks to portable PostgreSQL 16.15 (not Docker). Benchmarks:

```bash
cd backend
python scripts/bench_routing.py
```

Backend tests:

```bash
cd backend
pytest                                              # unit tests always; DB tests skip if Postgres is down
python -m app.seed --validate-only                  # graph integrity, no DB
python -m app.seed                                  # migrate first: alembic upgrade head
```

Regenerating the backend lockfile after changing `pyproject.toml`:

```bash
cd backend
pip install pip-tools
pip-compile --strip-extras pyproject.toml -o requirements-lock.txt
pip-compile --strip-extras --extra=dev pyproject.toml -o requirements-dev-lock.txt
```

Frontend:

```bash
cd frontend
npm ci                                              # deterministic install from lockfile
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
npm run lint && npm run typecheck && npm run test && npm run build
npx playwright test   # needs backend on :8000 and a seeded DB
```

## Documentation

Start here if you're reading this cold:

- [`docs/00-plan.md`](00-plan.md) — master plan: architecture, DB design, phases
- [`docs/01-problem-definition.md`](01-problem-definition.md) — personas, user stories, FR/NFR, scope, risks, success criteria
- [`docs/02-phase-1-design.md`](02-phase-1-design.md) — data model and NOVA seed
- [`docs/03-phase-2-routing.md`](03-phase-2-routing.md) — Dijkstra, A*, accessibility, benchmarks
- [`docs/04-phase-3-map-ui.md`](04-phase-3-map-ui.md) — SVG map, map API, route overlay
- [`docs/decisions/`](decisions/) — Architecture Decision Records
- [`docs/debugging/`](debugging/) — real bug postmortems (populated as bugs appear)
- [`docs/interview-notes.md`](interview-notes.md) — real stories from this project for interview prep

## Engineering decisions

Every important design choice gets an ADR. Current:

| # | Title |
|---|---|
| [001](decisions/001-modular-monolith.md) | Modular monolith over microservices |
| [002](decisions/002-astar-with-dijkstra-baseline.md) | A* for production, Dijkstra as baseline |
| [003](decisions/003-postgresql-with-pgvector.md) | PostgreSQL + pgvector for data and embeddings |
| [004](decisions/004-use-fastapi.md) | Use FastAPI for the backend |
| [005](decisions/005-pip-tools-for-locking.md) | pip-tools for Python dependency locking |
| [006](decisions/006-alembic-migration-strategy.md) | Alembic as the only schema-management strategy |
| [007](decisions/007-floor-local-coordinates.md) | Floor-local Cartesian coordinates |
| [008](decisions/008-directed-graph-edges.md) | Directed graph edges |
| [009](decisions/009-astar-heuristic-strategy.md) | Euclidean A* heuristic; no vertical bonus |
| [010](decisions/010-svg-for-indoor-map-rendering.md) | SVG for indoor map rendering |

## Phase 0b verification status

A piece of scaffolding being *written* is not the same as it being *verified*.
This table tracks the three verification tiers.

Legend:  ✅ verified locally   🤖 verified by CI (GitHub Actions)   ❌ attempted locally and failed   ⏸ not yet verified

| Check | Local | CI | Notes |
|---|---|---|---|
| Backend: Python files parse / byte-compile | ✅ | 🤖 | — |
| Backend: `ruff check` | ✅ | 🤖 | — |
| Backend: `ruff format --check` | ✅ | 🤖 | — |
| Backend: `pytest` (health endpoint tests, 2/2) | ✅ | 🤖 | DB-down branch verified locally; DB-up branch verified in CI with real Postgres |
| Backend: install from `requirements-dev-lock.txt` | ✅ | 🤖 | Deterministic install |
| Frontend: `npm ci` (lockfile install) | ✅ | 🤖 | — |
| Frontend: `npm run lint` (zero warnings) | ✅ | 🤖 | — |
| Frontend: `npm run typecheck` (strict TS) | ✅ | 🤖 | Caught `noPropertyAccessFromIndexSignature` issues |
| Frontend: `npm run build` (production build) | ✅ | 🤖 | 104 kB First Load JS |
| Frontend: `npm audit --omit=dev` (prod CVEs) | ✅ | — | 0 critical / 0 direct high after Next 15 upgrade; 2 nested postcss issues documented |
| Postgres container boots with pgvector + pg_trgm | ❌ | 🤖 (via `backend-ci.yml`) | **Failed locally 2026-10-06:** Docker CLI present, Linux engine stopped. Root cause: Virtual Machine Platform not enabled; Windows Home cannot use Hyper-V. See [`docs/debugging/2026-10-06-docker-engine-needs-virtual-machine-platform.md`](debugging/2026-10-06-docker-engine-needs-virtual-machine-platform.md) |
| `docker compose up --build` brings all services up | ❌ | — | Blocked on the same engine failure. Not marked complete. |
| `GET /api/v1/health` returns 200 with `db: ok` | ❌ | 🤖 (CI exercises against real Postgres) | Not verified through local compose |
| `http://localhost:3000` loads home + health probe shows green | ❌ | — | Not verified through local compose |
| `http://localhost:8000/docs` loads Swagger | ❌ | — | Not verified through local compose |
| Backend reaches Postgres via Docker DNS (`postgres:5432`) | ❌ | — | Not verified through local compose |
| Backend and Postgres containers report `healthy` | ❌ | — | Not verified through local compose |

See [`docs/debugging/`](debugging/) for every real issue found during verification.

## Phase 1 verification (real PostgreSQL 16.15)

Docker Compose is still blocked on this machine. Verification used a **portable PostgreSQL 16.15** with `vector` 0.8.6 and `pg_trgm` 1.6, not SQLite.

| Check | Result |
|---|---|
| `alembic upgrade head` on empty DB | ✅ created `malls`, `floors`, `categories`, `locations`, `map_nodes`, `map_edges` |
| `python -m app.seed` first successful insert | ✅ |
| `python -m app.seed` without `--force` | ✅ exit 2, refuses to overwrite |
| `python -m app.seed --force` | ✅ replaces the mall |
| pytest including Postgres tests | ✅ 21 passed, 0 skipped (with `DATABASE_URL` set) |

**Live `COUNT(*)` after seed (queried, not inferred):**

| table | rows |
|---|---|
| malls | 1 |
| floors | 3 |
| categories | 10 |
| locations | 31 |
| map_nodes | 91 |
| map_edges | 248 |

Seed is **intentionally not silent-idempotent**: a second run refuses unless `--force`. Re-running must not invent a merge of two graphs.

## Phase 2 verification (routing)

Docker Compose is still blocked. Algorithms run in-process; the HTTP route uses the same portable Postgres 16.15.

| Check | Result |
|---|---|
| `pytest` (backend, `DATABASE_URL` set) | ✅ **71 passed**, 0 skipped |
| Dijkstra vs A* cost equality (NOVA location pairs + grids) | ✅ equal cost |
| Wheelchair / avoid-stairs / one-way escalator | ✅ |
| `POST /api/v1/navigation/route` (Nike → Apple, wheelchair) | ✅ 200, uses elevator |
| Same location / unknown location | ✅ 400 / 404 |

**Measured `scripts/bench_routing.py` (this machine, 2026-10-06). `nodes_expanded` is deterministic; milliseconds are means.**

NOVA Mall seed graph: **V=91, E=248**.

| Route | Dijkstra expanded | A* expanded | A*/Dij | Dijkstra mean | A* mean |
|---|---|---|---|---|---|
| nike → zara (same floor) | 7 | 4 | 0.571 | 0.024 ms | 0.023 ms |
| parking → guest-services | 86 | 46 | 0.535 | 0.262 ms | 0.171 ms |
| main-entrance → muji (cross-floor) | 70 | 27 | 0.386 | 0.231 ms | 0.123 ms |
| nike → apple (time) | 68 | 30 | 0.441 | 0.224 ms | 0.118 ms |
| restroom G→L1 wheelchair | 83 | 41 | 0.494 | 0.272 ms | 0.152 ms |

Synthetic 4-connected grids, corner → opposite corner (Manhattan shortest path equals the graph diameter, so **every node is expanded** by both algorithms — not a bug):

| Grid | V | E | expanded (both) | Dijkstra mean | A* mean |
|---|---|---|---|---|---|
| 20×20 | 400 | 1,520 | 400 | 1.838 ms | 1.800 ms |
| 50×50 | 2,500 | 9,800 | 2,500 | 16.976 ms | 12.864 ms |
| 100×100 | 10,000 | 39,600 | 10,000 | 48.128 ms | 55.468 ms |

100×100 A* tracemalloc peak for one run: **1374.4 KiB**.

Re-run: `python scripts/bench_routing.py` from `backend/`.

Design: [`docs/03-phase-2-routing.md`](03-phase-2-routing.md), [ADR-009](decisions/009-astar-heuristic-strategy.md).

## Phase 3 verification (interactive map)

Same portable Postgres 16.15. The UI does not invent routes.

| Check | Result |
|---|---|
| `GET /api/v1/malls/nova-mall/map` | ✅ 3 floors, 31 locations, 91 nodes, 248 edges |
| Backend `tests/test_map_api.py` + navigation API (DATABASE_URL set) | ✅ 8 passed |
| Frontend lint (zero warnings) | ✅ |
| Frontend `tsc --noEmit` | ✅ |
| Frontend production build | ✅ 109 kB First Load JS |
| Vitest + Testing Library | ✅ **13 passed** |
| Playwright `e2e/navigation.spec.ts` | ✅ **1 passed** against live `127.0.0.1:8000` (health + map + A* route). Fails if the API is down. |

Map and route share one coordinate model (ADR-007 + ADR-010). See [`docs/04-phase-3-map-ui.md`](04-phase-3-map-ui.md).

## Phase 4 verification (search + assistant)

Same portable Postgres 16.15. Embeddings are local MiniLM (384). No chat API key.

| Check | Result |
|---|---|
| `python -m app.search.reindex` | ✅ 31 written, 0 failures |
| `python -m app.evaluation` | Lexical top-1 **12/13**, semantic **8/13**, hybrid **12/13** (top-3 **13/13**). Assistant templates **9/9**. |
| Backend pytest (`EMBEDDING_PROVIDER=none`) | ✅ **98 passed**. Ruff passed. |
| Frontend lint, `tsc`, Vitest, `next build` | ✅ 14 Vitest, First Load JS 110 kB |
| Browser | "Take me to Nike" drew the A* route (102 m). "Nkie" highlighted Nike. Gucci refused. Hebrew ATM and Arabic nearest restroom answered in that language and moved the map. |
| Live chat model | Pending |

Design: [`docs/05-phase-4-search-assistant.md`](05-phase-4-search-assistant.md), [ADR-011](decisions/011-hybrid-lexical-and-vector-search.md), [ADR-012](decisions/012-embedding-provider-abstraction.md), [ADR-013](decisions/013-tool-first-mall-assistant.md).

## Phase 5 verification (shopping tour)

Same portable Postgres 16.15. The planner does not replace A*. It orders stops.

| Check | Result |
|---|---|
| Canonical list (Entrance, Nike, Zara, Apple, ATM Ground, Super-Pharm) | Submitted **442.5 m**. Held-Karp **382.5 m**. Saved **60.0 m, 13.6%, 48 s**. Nearest Neighbor and 2-opt both **386.5 m** (+1.0%, 2-opt made 0 moves). |
| `scripts/bench_tour.py` | Held-Karp 17 ms at 10 stops, 89 ms at 12, 543 ms at 14. Exact cutoff is 12. Mean NOVA request at 20 stops: **118 ms**, 420 A* calls. |
| Backend pytest (`EMBEDDING_PROVIDER=none`) | ✅ **110 passed**. Ruff passed. |
| Frontend lint, `tsc`, Vitest, `next build` | ✅ 15 Vitest, First Load JS 113 kB |
| Browser | Plan tab. Five stops: 442.5 m → 382.5 m, order Entrance, ATM, Apple, Zara, Nike, Super-Pharm. Two stops already in order: "No shorter route was found." Level 1 shows only that floor's segment and keeps Apple's stop number. |
| Unreachable stop | Wheelchair across a stairs-only edge returns 422 and names the location. The plan does not drop it. |

Design: [`docs/06-phase-5-shopping-route.md`](06-phase-5-shopping-route.md), [ADR-014](decisions/014-shopping-route-optimization-strategy.md).

## Phase 6 verification (parking memory)

Parking memory is deliberately local-first: the level, zone, spot, optional note, and mapped parking entrance stay in browser storage. No location or vehicle data is sent to the backend. A saved entrance can become the destination of the existing A* route.

| Check | Result |
|---|---|
| Persist and restore a versioned parking record | ✅ Unit tested |
| Reject corrupt, cross-mall, oversized, or incomplete stored data | ✅ Unit tested |
| Save, display, clear, and route to a mapped entrance | ✅ Component tested |
| Browser storage failure | ✅ Reported without losing the running app |

Design: [`docs/07-phase-6-parking-memory.md`](07-phase-6-parking-memory.md), [ADR-015](decisions/015-device-local-parking-before-auth.md).

**Not started:** accounts and cross-device parking sync. Do not present device-local storage as authenticated cloud persistence.

## Project layout

```
mallmind/
├── backend/
│   ├── app/
│   │   ├── api/v1/             # thin routers
│   │   ├── core/               # config, database
│   │   ├── models/             # SQLAlchemy tables
│   │   ├── schemas/            # Pydantic (seed document)
│   │   ├── routing/            # Dijkstra, A*, heuristic, instructions
│   │   ├── search/             # lexical bands, embeddings, reindex
│   │   ├── assistant/          # intent, tools, prompts, templates
│   │   ├── evaluation/         # curated search + assistant cases
│   │   ├── repositories/       # seed + graph load
│   │   ├── services/           # seed apply / navigation
│   │   ├── seed/               # NOVA Mall builder + validator + CLI
│   │   └── main.py
│   ├── alembic/versions/       # versioned schema
│   ├── scripts/bench_routing.py
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/app/
│   ├── src/components/{map,navigation,search,assistant,parking}
│   ├── src/lib/
│   ├── e2e/
│   ├── public/
│   └── Dockerfile
├── .github/workflows/
├── docker-compose.yml
└── docs/
    ├── 02-phase-1-design.md
    ├── 04-phase-3-map-ui.md
    ├── decisions/
    └── debugging/
```

## License

MIT. See [`LICENSE`](../LICENSE).
