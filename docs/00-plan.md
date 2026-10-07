# MallMind — Project Plan

> This is the master plan written at project start. It is a snapshot, not a living document.
> When any part of it changes materially, write an ADR explaining why and update the "Status" line below.

**Status:** Approved, 2026-10-05 — **Phase 5 implemented** (open shopping tour on the existing A* matrix). Live chat-model verification is still pending (no `LLM_API_KEY`). Phase 0b Docker Compose remains failed locally (VMP). Stop before auth and parking.

---

## 1. The problem

Large shopping malls are navigationally hostile. Outdoor map providers stop at the door. Printed floor directories are static and rarely consulted. Per-mall apps exist but have near-zero adoption for one-off visits.

Concrete pain points MallMind addresses:

| Pain | Who feels it | Current workaround |
|---|---|---|
| "Where is store X?" | First-time visitors | Walk around; ask info desk |
| "Nearest bathroom?" | Everyone | Guess |
| "Fastest route to visit 4 stores" | Shoppers with a list | Walk inefficiently; backtrack |
| "I can't use stairs" | Wheelchair users, parents with strollers, elderly | Avoid the mall entirely |
| "Where did I park?" | Everyone, after 2 hours of shopping | Photos, luck |
| "Ask in my own language" | Tourists, Arabic/Hebrew speakers | None |

The engineering value is not in drawing a pretty map. The engineering value is in graph modeling, shortest-path algorithms on a weighted multi-floor graph, cost functions for accessibility, TSP heuristics for multi-stop tours, RAG grounding for an LLM, and an API that composes these cleanly.

---

## 2. MVP scope

Four features, each done well.

1. **Indoor navigation** — single pair of points, A*, multi-floor, text + visual directions.
2. **Accessible routing** — same algorithm, different cost function.
3. **Hybrid search** — SQL text search + semantic vector search, ranked merge.
4. **AI assistant** — RAG over mall data; refuses to answer when it has no grounding.

Phase 2 (after MVP works):

5. **Multi-stop route optimization** — nearest-neighbor TSP heuristic.
6. **Parking memory** — simple CRUD with auth.
7. **User accounts + favorites.**

---

## 3. System architecture

Modular monolith. One backend process. One database. One frontend.

```
                    ┌───────────────────────┐
                    │  Next.js (TypeScript) │
                    │  SSR + Client Islands │
                    └──────────┬────────────┘
                               │  HTTPS / REST (JSON)
                               ▼
                    ┌───────────────────────┐
                    │   FastAPI (Python)    │
                    │  routers → services   │
                    │  → repositories       │
                    │  → algorithms         │
                    │                       │
                    │  In-memory graph      │
                    │  cache (loaded on     │
                    │  startup)             │
                    └──────┬──────────┬─────┘
                           │          │
                           ▼          ▼
                 ┌─────────────┐  ┌─────────────┐
                 │ PostgreSQL  │  │  LLM API    │
                 │ + pgvector  │  │ (TBD —      │
                 │             │  │ deferred to │
                 │ - app data  │  │  Phase 5)   │
                 │ - vectors   │  └─────────────┘
                 └─────────────┘
```

See [`decisions/001-modular-monolith.md`](decisions/001-modular-monolith.md) for the rationale.

**Hot-path optimization that matters:** the mall graph lives in RAM, loaded once from Postgres at startup. A* runs on in-memory structures (microseconds per query) instead of hitting the DB per node expansion.

---

## 4. Database design

### Tables (MVP)

| Table | Purpose |
|---|---|
| `malls` | Future-proof even with one mall. |
| `floors` | Levels in a mall. |
| `categories` | Store taxonomy. |
| `locations` | Stores + facilities + POIs. Anchored to one `map_node`. |
| `map_nodes` | Graph vertices. `(floor_id, x, y, node_type)`. |
| `map_edges` | Graph edges, directed. `(from, to, distance_m, edge_type, accessible, avg_seconds)`. |
| `users` | Auth. |
| `parking_locations` | Users remember spots. Partial unique index on `(user_id) WHERE is_current`. |
| `document_chunks` | RAG corpus. `embedding vector(1536)` + metadata. |
| `navigation_history` | Analytics + debugging. |

### Index strategy — driven by actual queries

| Query | Index |
|---|---|
| `WHERE name ILIKE '%nike%'` | GIN trigram index on `locations.name` |
| `WHERE category_id = ? AND floor_id = ?` | B-tree composite `(floor_id, category_id)` |
| Load graph edges by source | B-tree on `map_edges.from_node_id` |
| Nearest-vector for RAG | HNSW on `document_chunks.embedding` |
| Parking "current" lookup | Partial unique on `parking_locations(user_id) WHERE is_current` |

Stay at **3NF**. One deliberate denormalization: `location.node_id` caches the anchor node to avoid a join on every route request.

---

## 5. The mall graph

Weighted, directed, multi-floor graph.

**Node types:** `STORE`, `HALLWAY_JUNCTION`, `ELEVATOR`, `STAIRS`, `ESCALATOR_UP`, `ESCALATOR_DOWN`, `ENTRANCE`, `EXIT`, `BATHROOM`, `ATM`, `INFO_DESK`.

**Edge properties:** `distance_m`, `edge_type` (walk / stairs / elevator / escalator), `accessible` (bool), `avg_seconds`.

**Multi-floor technique:** an elevator at `(x, y)` on Floor 1 is a *different node* from the one at `(x, y)` on Floor 2. They are connected by an `elevator` edge with `distance_m = 0`, `avg_seconds = 30` (ride+wait penalty), `accessible = true`. Stairs follow the same pattern but `accessible = false`, `avg_seconds = 15`.

**In-memory representation:** adjacency list — `dict[NodeId, list[Edge]]` plus `dict[NodeId, Node]` for coordinates. Chosen over matrix because the graph is sparse (each node has 2–8 neighbors).

**Edge cases to handle:**

- Disconnected graph → return "no route found" (never crash).
- Start == goal → zero-length route with one node.
- Store without an anchor node → caught at seed time; seeder refuses.
- Stale in-memory graph after admin edit → `POST /admin/graph/reload`.

---

## 6. A* vs Dijkstra

Both find the shortest path in a weighted graph with non-negative edges.

| | Dijkstra | A* |
|---|---|---|
| Explores | Uniformly outward from start | Biased toward the goal via `h(n)` |
| Time (worst case) | O((V+E) log V) | O((V+E) log V), typically far fewer expansions |
| Needs | Graph only | Graph + admissible heuristic |
| Negative weights | No | No |

**Why A*:** we have `(x, y, floor)` coordinates, so Euclidean distance is a free admissible heuristic.

**Why we implement both:** educational value, cross-check for A*'s correctness, and benchmark comparison. See [`decisions/002-astar-with-dijkstra-baseline.md`](decisions/002-astar-with-dijkstra-baseline.md).

**Scaling note:** 2,000 nodes = milliseconds. 100,000 nodes would call for landmark-based heuristics (ALT) or contraction hierarchies — out of scope for this project.

---

## 7. API design

Versioned REST, JSON, consistent error envelope.

```
GET    /api/v1/health
GET    /api/v1/locations?q=&category=&floor=&kind=
GET    /api/v1/locations/{id}
GET    /api/v1/search?q=&mode=hybrid|text|semantic
POST   /api/v1/navigation/route
POST   /api/v1/navigation/optimize-tour          # Phase 2
POST   /api/v1/assistant/query
POST   /api/v1/auth/signup
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
GET    /api/v1/parking/current                   # auth
POST   /api/v1/parking                           # auth
DELETE /api/v1/parking/{id}                      # auth
```

Error contract: `{code, message, details?}` with meaningful HTTP status. Validation at the router boundary with Pydantic.

---

## 8. Folder structure

```
mallmind/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/           # config, db, security, logging
│   │   ├── api/v1/         # thin routers
│   │   ├── services/       # business logic
│   │   ├── repositories/   # DB access
│   │   ├── algorithms/     # pure functions (A*, Dijkstra, NN)
│   │   ├── rag/
│   │   ├── graph/          # in-memory loader + registry
│   │   ├── models/         # SQLAlchemy
│   │   └── schemas/        # Pydantic
│   ├── alembic/
│   ├── seed/
│   ├── tests/{unit,integration,e2e}
│   └── Dockerfile
├── frontend/
│   ├── src/{app,components,lib,hooks}
│   ├── tests/e2e/
│   └── Dockerfile
├── docker-compose.yml
├── .github/workflows/
└── docs/
    ├── decisions/
    └── debugging/
```

**Why layered backend?** Each layer has one reason to change. Router = HTTP contract. Service = business rules. Repository = DB schema. Algorithm = math. This is testability and portability by design.

**Where we won't overengineer:** no interfaces/ABCs for repositories until a second implementation exists.

---

## 9. Development phases

| Phase | Days | Goal | Done when… |
|---|---|---|---|
| **0a. Documentation** | 1 | Problem definition, ADRs, folder plan | ✅ Done |
| **0b. Scaffolding** | 2 | Repo, docker-compose, FastAPI `/health`, Next.js home, CI lint+test, lockfiles | Partial: code + CI ✅; local `docker compose up` ❌ (VMP) |
| **1. Data model + seed** | 3 | Migrations, seed from the HTML prototype | ✅ Alembic + NOVA seed on portable PG 16.15 |
| **2. A* + Dijkstra + accessible mode** | 5 | Pure functions, unit-tested; HTTP route | ✅ 71 pytest; real benches; stop before map UI |
| **3. Nav API + minimal map UI** | 4 | `POST /navigation/route` + SVG renderer with path overlay | Click origin → destination and see a real A* overlay |
| **4. Hybrid search + assistant** | 3 | Trigram + semantic + ranked merge; tool-first answers | ✅ Lexical 12/13, hybrid 12/13 top-1 and 13/13 top-3. Gucci refused. Live LLM pending. |
| **5. Multi-stop tour** | 2 | Open tour on the existing A* matrix | ✅ Held-Karp through 12 stops, NN + 2-opt after. Canonical NOVA list 442.5 m → 382.5 m. ADR-014. |
| **6. TSP tour optimizer** | 2 | Same work as Phase 5 | Do not schedule twice. Shipped as Phase 5. |
| **7. Auth + parking** | 2 | JWT, bcrypt, parking CRUD | Login → save spot → retrieve |
| **8. Testing polish + Playwright** | 3 | 3 happy-path E2Es; raise service coverage | CI green on all three test tiers |
| **9. Deploy** | 2 | Cloud deploy + live demo link | Public URL in README |

**Ordering rationale:** algorithms first. If routing is wrong, nothing matters. Build the hardest, highest-risk piece first; UI wraps a correct backend later.

---

## 10. Top-10 engineering decisions (summary)

Each becomes a dedicated ADR as we hit it. Status column tracks progress.

| # | Decision | ADR | Status |
|---|---|---|---|
| 1 | Modular monolith over microservices | `001-modular-monolith.md` | ✅ Written |
| 2 | PostgreSQL + pgvector over separate vector DB | `003-postgresql-with-pgvector.md` | ✅ Written |
| 3 | A* with Dijkstra as a baseline (both implemented) | `002-astar-with-dijkstra-baseline.md` | ✅ Written |
| 4 | FastAPI over Flask / Django | `004-use-fastapi.md` | ✅ Written |
| 5 | pip-tools for deterministic Python dependency locking | `005-pip-tools-for-locking.md` | ✅ Written |
| 6 | In-memory graph, DB as source of truth | `03-phase-2-routing.md` + ADR-009 | ✅ Phase 2 loads per request; cache later |
| 7 | RAG with strict grounding over fine-tuning | `013-tool-first-mall-assistant.md` | ✅ Phase 4. Templates when the model is absent. Live key pending. |
| 8 | Hybrid search (SQL text + vector) | `011-hybrid-lexical-and-vector-search.md` | ✅ Phase 4. Eval numbers in `05-phase-4-search-assistant.md`. |
| 9 | JWT access + refresh over sessions | TBD | Pending (Phase 7) |
| 10 | TypeScript strict mode, zero `any` | `frontend/tsconfig.json` | ✅ Phase 3 (no codegen, no `any`) |
| 11 | Pytest-heavy, Playwright-light test pyramid | TBD | Pending (Phase 8); first Playwright route test in Phase 3 |

## Open decisions

| # | Decision | Blocking? | When needed |
|---|---|---|---|
| LLM provider (OpenAI-compatible HTTP). Local MiniLM is the embedder. | No | Chat key still unset after Phase 5 |
| Open tour vs a required final door | No | Phase 5 shipped the open tour. A fixed end would extend ADR-014, not replace A*. |
| Cloud target (Azure App Service / Container Apps / other) | No | Phase 9 |
