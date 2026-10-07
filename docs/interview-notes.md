# Interview Notes

**Not** a generic interview prep file. This document only contains things that **actually happened** during MallMind development: decisions, bugs, benchmarks, trade-offs, and lessons.

The purpose is a single place to grab authentic material when preparing for an interview. If a question would be answered by a story in this file, I can speak from real work.

## Rules for adding entries

- Only write things that came from **real** work on this project.
- Prefer specific numbers, file paths, and dates over generalities.
- Each entry should answer a plausible interview question.
- Keep each entry short enough to be *said out loud* in 1–2 minutes.

## Format

```markdown
### Topic — one-line summary

**Likely interview question:** "..."

**Short answer (90 seconds, out loud):**
...

**Deeper detail if asked:**
...

**Source:** link to ADR / commit / bug postmortem / benchmark output.
```

---

## Entries

### Architecture — Why a modular monolith instead of microservices?

**Likely interview question:** *"Why didn't you go with microservices?"*

**Short answer (90 seconds, out loud):**
MallMind is a single-developer project with four cohesive subsystems — navigation, search, assistant, parking — that share one domain model. Microservices optimize for independent teams and independent scaling; I had neither. The real cost of microservices is operational: service discovery, inter-service auth, distributed tracing, and distributed transactions. All of that is cost I didn't need to pay. I built a modular monolith with strict layering so I could extract a module into a service later if load ever justified it — but I'd pay that cost only when it was earned.

**Deeper detail if asked:**
Each module is layered router → service → repository → algorithm. The service layer never imports FastAPI; the algorithm layer never touches the database. That boundary is what makes extraction cheap later, and it's what makes the business logic unit-testable without a database.

**Source:** [`decisions/001-modular-monolith.md`](decisions/001-modular-monolith.md).

---

### Database — Why PostgreSQL + pgvector instead of a dedicated vector DB?

**Likely interview question:** *"Why not Pinecone or Weaviate for the vector search?"*

**Short answer (90 seconds, out loud):**
My corpus is in the low thousands of chunks, not millions. At that scale, pgvector with an HNSW index does the job well under 50 ms. The hidden cost of a second database isn't performance — it's operational: two sets of credentials, two backup policies, two monitoring dashboards, and consistency between them becomes an application concern. Keeping everything in Postgres also lets me write hybrid search as a single SQL query that combines `WHERE name ILIKE %q%` with `ORDER BY embedding <=> query`.

**Deeper detail if asked:**
I'd reconsider at ~10M+ vectors with hard P95 SLOs, or if we needed features pgvector doesn't have — sparse-dense hybrid rerankers, multi-vector-per-document, etc.

**Source:** [`decisions/003-postgresql-with-pgvector.md`](decisions/003-postgresql-with-pgvector.md).

---

### Algorithms — Why A* instead of Dijkstra, and how do you know it's correct?

**Likely interview question:** *"How do you know your A* implementation returns optimal paths?"*

**Short answer (90 seconds, out loud):**
I use A* in production because I have `(x, y, floor)` coordinates for every graph node, which gives me a free admissible heuristic — straight-line distance. A* with an admissible heuristic is strictly ≥ Dijkstra: in the worst case it degrades to Dijkstra, in the typical case it explores a fraction of the nodes. To prove correctness, I also implemented Dijkstra as a reference, and every A* test fixture is cross-checked: A* and Dijkstra must return paths of equal cost on the same input. If my A* ever became buggy — wrong tiebreak, missed closed-set update, bad reconstruction — the Dijkstra cross-check would catch it immediately.

**Deeper detail if asked:**
One subtle correctness detail: if I optimize on *time* (including elevator wait), a distance-based heuristic *underestimates* true cost on different-floor routes. Underestimates are fine — they preserve admissibility and therefore optimality. Overestimates would break it. The ADR documents this explicitly so future me doesn't accidentally "tighten" the heuristic into incorrectness.

**Source:** [`decisions/002-astar-with-dijkstra-baseline.md`](decisions/002-astar-with-dijkstra-baseline.md).

---

### Debugging — Real bug caught by the first test run on a fresh scaffold

**Likely interview question:** *"Tell me about a tricky bug you had to debug."*

**Short answer (90 seconds, out loud):**
Right after I scaffolded the backend, I ran the health-endpoint tests with no Postgres running — the test deliberately wanted to prove the endpoint reports "degraded" instead of crashing. It failed. The handler was returning 500 instead of 503. I traced it: my `except` clause caught `SQLAlchemyError`, but asyncpg's connect-time failures are raised as plain `ConnectionRefusedError` on some code paths — `OSError`, not `SQLAlchemyError`. SQLAlchemy *does* usually wrap DBAPI errors into `OperationalError`, but on connect-time asyncpg failures it re-raises the OS error without wrapping. My net was too narrow. I changed the except to `Exception` with a `# noqa: BLE001` and a docstring explaining why the broad catch is intentional for health endpoints. Tests passed, and I wrote the whole thing up as `docs/debugging/2026-10-05-...`.

**Deeper detail if asked:**
The general rule I take from this is that health endpoints belong to the operational interface, not the application interface. A 500 is worse than a 503 — orchestrators treat 503 as "take me out of rotation" and 500 as "transient, retry." The "don't swallow exceptions" rule has an explicit exception for health checks, and I'd failed to extend the pattern consistently from the lifespan hook (which already caught broadly) to the request handler.

**Source:** [`debugging/2026-10-05-health-endpoint-missed-connectionrefused.md`](debugging/2026-10-05-health-endpoint-missed-connectionrefused.md).

---

### Supply chain — Why I upgraded Next.js on day one and what I learned about pinning

**Likely interview question:** *"How do you handle security of your project's dependencies?"*

**Short answer (90 seconds, out loud):**
During scaffolding verification I ran my first `npm install` and `npm audit` reported 10 vulnerabilities including a Next.js critical — RCE on Windows self-hosted deploys. I'd pinned Next 14.2.15 without checking it was still current, and several criticals aren't backported to the 14.x line at all. I upgraded to Next 15.5.27 — the current major, old enough to be stable, new enough to be patched. That one change dropped production-only audit output from 10 vulnerabilities to 2, both nested postcss issues inside Next's build tooling that are only exploitable against attacker-controlled CSS. I accepted those as documented residual risk. The whole investigation went into `docs/debugging/`. Then I added lockfiles — `package-lock.json` for the frontend and pip-tools-generated `requirements-lock.txt` for the backend — plus switched CI to `npm ci` and `pip install -r …-lock.txt` so every build installs exactly what was reviewed. ADR 005 documents the pip-tools decision; I didn't want to introduce a new installer like Poetry just to get locking.

**Deeper detail if asked:**
The general lesson I took away: a version pin is a promise about resolution, not about safety. "Pin everything" is sometimes framed as a security best practice, but a stale pin is a decaying security posture. The real safety move is: pin + run audit regularly + have a lockfile so you can tell when transitive versions actually shifted.

**Source:** [`debugging/2026-10-05-frontend-cve-surge-on-first-install.md`](debugging/2026-10-05-frontend-cve-surge-on-first-install.md), [`decisions/005-pip-tools-for-locking.md`](decisions/005-pip-tools-for-locking.md).

---

### Infra — Docker Desktop installed is not the same as an engine that can run Linux containers

**Likely interview question:** *"Your README says Docker Compose. Did you actually run it?"*

**Short answer (90 seconds, out loud):**
I did not mark it verified. `docker version` showed a working Windows client and then HTTP 500 against `dockerDesktopLinuxEngine`. Desktop and `com.docker.backend` were running. The backend log said the linux/wsl engine went starting → stopped in 20 ms: Virtual Machine Platform not enabled. This machine is Windows Home, so Hyper-V is not an alternative. I treated "CLI on PATH" and "engine actually running" as two different facts, left the verification matrix as failed, and wrote the postmortem instead of claiming compose was green.

**Deeper detail if asked:**
`wsl --status` printing install-usage text means you have the inbox stub, not WSL. Enabling VMP/WSL needs elevation and a reboot. That is a host change, not an application fix.

**Source:** [`debugging/2026-10-06-docker-engine-needs-virtual-machine-platform.md`](debugging/2026-10-06-docker-engine-needs-virtual-machine-platform.md).

---

### Data model — Why Location and MapNode are different tables

**Likely interview question:** *"Why isn't a store just a node in the graph?"*

**Short answer (90 seconds, out loud):**
A location is something a person searches for. A map node is a vertex A* will expand. Most vertices are hallway junctions and landings — they must not appear in search. A store's catalog identity should survive us splitting a corridor into more nodes. In Phase 1 the link is `map_nodes.location_id` nullable unique: at most one anchor per location, most nodes have no location. When a store gets a second entrance, we drop the unique constraint instead of turning Location into a graph vertex.

**Deeper detail if asked:**
Putting `map_node_id` on Location would work for 1:1 and then rot into `primary_node_id` plus a join table. Starting the FK on the node side is the 1:N-ready shape.

**Source:** [`02-phase-1-design.md`](02-phase-1-design.md), [`decisions/007-floor-local-coordinates.md`](decisions/007-floor-local-coordinates.md).

---

### Graph — Why edges are directed rows, not an `is_bidirectional` flag

**Likely interview question:** *"Won't you store twice as many hallway edges?"*

**Short answer (90 seconds, out loud):**
Yes, and that is the point. Escalators are one-way. A* should be "expand outgoing neighbours" with no special case. Two rows also let up-elevator and down-elevator wait times diverge later without a schema change. The seed generator emits both directions for hallways, elevators, and stairs; the validator does not silently insert a missing reverse, because a missing reverse might be a real one-way corridor.

**Source:** [`decisions/008-directed-graph-edges.md`](decisions/008-directed-graph-edges.md).

---

### Schema — Why Alembic instead of `create_all()`, and why the first migration is hand-written

**Likely interview question:** *"Why not let SQLAlchemy create the tables?"*

**Short answer (90 seconds, out loud):**
`create_all()` cannot rename a column, cannot add a CHECK cleanly, and has no history. Alembic gives us a git-reviewed path from an empty database to the current schema — the same path CI will use. Autogenerate is a draft. The first migration is hand-written because it creates Postgres ENUMs (`node_type`, `edge_type`) and extensions (`vector`, `pg_trgm`). Alembic autogenerate is unreliable on those.

**Source:** [`decisions/006-alembic-migration-strategy.md`](decisions/006-alembic-migration-strategy.md).

---

### Constraints — What belongs in PostgreSQL vs the Python seed validator

**Likely interview question:** *"Why not put all graph rules in CHECK constraints?"*

**Short answer (90 seconds, out loud):**
If a bad row would silently break production and the check does not need a join, it goes in Postgres: unique slugs, `distance_m >= 0`, `avg_seconds > 0`, no self-loops, unique `(from, to)`. "This elevator edge stacks at the same (x, y) on two different floors" needs a self-join. "Every store is reachable from an entrance" needs BFS. Those live in the validator, which fails the whole seed and lists every problem instead of repairing data.

**Source:** [`02-phase-1-design.md`](02-phase-1-design.md).

---

### Routing — Why an adjacency list, not a matrix

**Likely interview question:** *"How did you represent the mall graph in memory?"*

**Short answer (90 seconds, out loud):**
NOVA Mall is 91 nodes and 248 directed edges — about 2.7 neighbours per vertex. That's a sparse corridor graph, not a complete graph. An adjacency list is `O(V+E)` space and `O(degree)` to expand a node. A matrix would be `O(V²)` memory and `O(V)` to scan a row even when the degree is 2. Dijkstra and A* are `O((V+E) log V)` on a binary heap plus that list. I would only reach for a matrix if I had a dense graph or needed `O(1)` "is this edge present?" with `V` still tiny. Our 100×100 synthetic grid already has 10,000 vertices; a matrix would be 100 million slots for a 4-connected mesh.

**Source:** [`03-phase-2-routing.md`](03-phase-2-routing.md).

---

### Routing — Why Dijkstra still exists if A* is production

**Likely interview question:** *"If A* is optimal, why keep Dijkstra?"*

**Short answer (90 seconds, out loud):**
A* is optimal *if* the heuristic is admissible. That "if" is an implementation hazard — a closed-set bug, a time/distance unit mismatch, a "clever" elevator bonus that overestimates. Dijkstra does not use `h`, so it is an oracle. Every NOVA location pair is asserted equal-cost between the two. On 2026-10-06 that was 31×31 pairs in both distance and time. Production `POST /api/v1/navigation/route` calls A*. The suite and the benchmark script call both.

**Deeper detail if asked:**
The files are separate on purpose. Sharing the heap loop would make a bug copy itself into the oracle. They share only path reconstruction.

**Source:** [`decisions/002-astar-with-dijkstra-baseline.md`](decisions/002-astar-with-dijkstra-baseline.md), [`decisions/009-astar-heuristic-strategy.md`](decisions/009-astar-heuristic-strategy.md).

---

### Routing — Directed edges made escalators free

**Likely interview question:** *"How do you stop someone walking down an up escalator?"*

**Short answer (90 seconds, out loud):**
I don't. The algorithm has no escalator branch. The seed inserts `ESCALATOR_UP` as one directed row and never inserts the reverse. A* expands `outgoing[u]`. There is no down edge, so there is no down ride. The unit test is a two-node graph with only that edge: ground→L1 succeeds, L1→ground is `no_path`. Hallways still get two rows because they *are* two-way. Putting direction in the data kept the 60-line routers boring, which is what I wanted.

**Source:** [`decisions/008-directed-graph-edges.md`](decisions/008-directed-graph-edges.md), `backend/tests/test_escalator.py`.

---

### Routing — Accessibility is an edge predicate

**Likely interview question:** *"Did you implement three A*s for wheelchair mode?"*

**Short answer (90 seconds, out loud):**
No. Dijkstra and A* take `allow(edge) -> bool`. `WHEELCHAIR` is `edge.accessible`. `AVOID_STAIRS` is `edge_type is not STAIRS`. On NOVA, west-side restrooms (ground north → L1) use the stairs under `NORMAL` and the elevator under `WHEELCHAIR`. A stairs-only toy graph returns `no_path` for wheelchair and a path for normal. If I had copied the algorithm, a closed-set fix would need three patches.

**Source:** `backend/app/routing/policy.py`, `backend/tests/test_accessibility.py`.

---

### Routing — What the benchmarks actually showed

**Likely interview question:** *"Is A* faster than Dijkstra in your system?"*

**Short answer (90 seconds, out loud):**
On the real mall graph, yes, in expansions: 38–57% of Dijkstra's nodes at equal cost. Nike→Zara is 44 m, 7 vs 4 expansions. Main entrance→Muji is 118 m, 70 vs 27. Wall-clock on that graph is a fraction of a millisecond either way, so I would not sell latency. On a filled 4-connected 100×100 grid, corner to corner, A* expanded *all 10,000 nodes* — same as Dijkstra — and the mean was *worse* (55.5 ms vs 48.1 ms) because `hypot` is extra work that did not prune. Every cell sits in the start–goal rectangle, so Euclidean `f*` never exceeds Manhattan `C*`. That is why I kept Dijkstra and why I did not cache, rewrite in C++, or "tighten" the heuristic with an elevator bonus.

**Source:** [`03-phase-2-routing.md`](03-phase-2-routing.md) (table from `python scripts/bench_routing.py` on 2026-10-06).

---

### Map UI — Why SVG instead of Canvas or a mapping library?

**Likely interview question:** *"Why didn't you use Mapbox / Canvas for the indoor map?"*

**Short answer (90 seconds, out loud):**
The routing graph already has floor-local `(x, y)`. I needed clickable stores, floor tabs, an A* polyline, and a debug overlay that shows the vertices the heap actually searched. SVG gives me DOM, accessibility, and inspectable paths. Canvas makes hit-testing and a11y my problem. MapLibre is GIS; this is a 120×90 schematic with 91 nodes. I flip `y` once because backend y is north and SVG y is down. The browser never runs A* — it joins `node_ids` from `POST /navigation/route` onto those coordinates.

**Deeper detail if asked:**
Search keystrokes stay inside `LocationSearch` so the SVG does not re-render per character. We fetch the whole mall map once; floor switches are a filter. I skipped Redux because the state is one screen: floor, two ids, profile, last route, debug toggle.

**Source:** [`decisions/010-svg-for-indoor-map-rendering.md`](decisions/010-svg-for-indoor-map-rendering.md), [`04-phase-3-map-ui.md`](04-phase-3-map-ui.md).

---

### Map UI — Frontend is not a second source of truth

**Likely interview question:** *"How do you keep the map and the router from drifting apart?"*

**Short answer (90 seconds, out loud):**
There is one coordinate model in Postgres. The map endpoint and the graph loader read the same `map_nodes` / `map_edges` / `locations`. The UI is allowed to style and to remember which floor you are looking at. It is not allowed to invent a corridor or a shortcut. If the orange path disagrees with A*, the SVG is wrong.

**Source:** [`04-phase-3-map-ui.md`](04-phase-3-map-ui.md).

---

### Search — Exact names have to beat the embedding

**Likely interview question:** *"Why not just embed everything and skip keyword search?"*

**Short answer (90 seconds, out loud):**
On NOVA, with multilingual MiniLM, the query "Nike" is closer to Adidas (cosine 0.441) than to Nike's own passage (0.388). "Gucci" is closest to Sushi Kaito (0.427). A nearest-neighbor search will always return a store. Hybrid search returns the lexical hit when we have one, and returns nothing for a short name we do not have. On a 13-query set, lexical and hybrid were 12/13 at top-1. Semantic was 8/13. The one hybrid miss is "footwear for jogging today", where Adidas beat Nike by 0.019. I left that number in the doc.

**Source:** [`05-phase-4-search-assistant.md`](05-phase-4-search-assistant.md), [`decisions/011-hybrid-lexical-and-vector-search.md`](decisions/011-hybrid-lexical-and-vector-search.md).

---

### Search — pg_trgm's 0.3 cutoff drops "Nkie"

**Likely interview question:** *"How does your typo search work?"*

**Short answer (90 seconds, out loud):**
I measured it. `similarity('nkie','nike')` is 0.11. `similarity('gucci','Guest Services')` is 0.105. Dropping the cutoff to 0.10 would "fix" Nkie and also return Guest Services for Gucci. A 4-letter transposition destroys padded trigrams. One Damerau edit still sees it, so that case scores 0.80, inside the trigram band and under a prefix. Longer typos like "starbuks" (0.58) stay on pg_trgm.

**Source:** [`debugging/2026-10-06-trigram-short-name.md`](debugging/2026-10-06-trigram-short-name.md).

---

### Search — Why pgvector, still

**Likely interview question:** *"Why not Pinecone?"*

**Short answer (90 seconds, out loud):**
Thirty-one vectors of 384 dimensions. They sit in the same transaction as the location row. Reindex skips a row when the passage hash and the model name already match. A second database would be a second catalog to get wrong. HNSW is there. We are nowhere near the scale where it matters.

**Source:** [`decisions/003-postgresql-with-pgvector.md`](decisions/003-postgresql-with-pgvector.md), [`decisions/012-embedding-provider-abstraction.md`](decisions/012-embedding-provider-abstraction.md).

---

### Assistant — The model does not calculate the route

**Likely interview question:** *"How do you stop the assistant inventing a path?"*

**Short answer (90 seconds, out loud):**
Python decides the tool. "Take me to Nike" resolves both ends and calls the same A* service the map uses. The sentence quotes that distance. In a unit test the fake model says the walk is 1 meter through a secret corridor. The answer still says 102 m, and the model is not called at all for routes. "Where is Gucci?" never calls the model: retrieval is empty. If a model is configured and writes "Nike is next to Gucci on Floor 9", that text is rejected and the template says Ground Floor. I have not pointed this at a paid chat API. There is no key. A client pointed at port 9 fails closed and the template still answers.

**Source:** [`decisions/013-tool-first-mall-assistant.md`](decisions/013-tool-first-mall-assistant.md), `backend/tests/test_assistant_unit.py`.

---

### Assistant — Hebrew "the" is a prefix, not a word

**Likely interview question:** *"What did multilingual eval actually show?"*

**Short answer (90 seconds, out loud):**
`איפה יש כספומט` found the ATM, because the synonym is the bare noun. `איפה הכספומט?` did not, until I stopped searching the raw sentence. The ה is "the", glued to the noun. The embedding of the bare Hebrew token was worse: nearest store was Muji at 0.336, under the floor, so vectors did not save it. Keywords did. Arabic "وين أقرب حمام؟" routed to Restroom — Ground South, 80 m, and the store name stayed in English inside an Arabic sentence. I would not advertise the embedding model as multilingual on this catalog. I would advertise the synonym list.

**Source:** [`debugging/2026-10-06-hebrew-definite-article.md`](debugging/2026-10-06-hebrew-definite-article.md), [`05-phase-4-search-assistant.md`](05-phase-4-search-assistant.md).

---

### Tours — A* prices a pair. It does not order the shops.

**Likely interview question:** *"You already have A*. Why isn't that the shopping planner?"*

**Short answer (90 seconds, out loud):**
A* is start to one destination. A list is start, then several stops, in some order, and the shopper does not walk back to the door. That is an open tour. With the start fixed, 5 stops is 120 orders, 10 is 3.6 million, 20 is 2.43 × 10^18. I still call A* for every directed pair and build a matrix. Five stops is 30 calls. The optimizer only sees that matrix. On NOVA, Main Entrance then Nike, Zara, Apple, the ground ATM, and Super-Pharm is 442.5 m in the typed order and 382.5 m after Held-Karp: Entrance, ATM, Apple, Zara, Nike, pharmacy. Sixty metres, 13.6 percent, 48 seconds.

**Deeper detail if asked:**
Nearest Neighbor on that list was 386.5 m, 1.0 percent over the optimum, and 2-opt did not move. The exact solver is what saved the last 4 m. I do not call the heuristic optimal.

**Source:** [`06-phase-5-shopping-route.md`](06-phase-5-shopping-route.md), [`decisions/014-shopping-route-optimization-strategy.md`](decisions/014-shopping-route-optimization-strategy.md).

---

### Tours — Held-Karp until the clock says stop

**Likely interview question:** *"Why keep an exact solver if you also have a heuristic?"*

**Short answer (90 seconds, out loud):**
So I can measure the heuristic. Held-Karp is `O(2^k k^2)` time and `O(2^k k)` memory, start fixed, no return. On random directed matrices, CPython 3.12: 17 ms at 10 stops, 89 ms at 12, 543 ms at 14. The API uses the DP through 12 stops and Nearest Neighbor plus 2-opt after that. Twenty stops is the hard cap. The mean NOVA request at 20, heuristic only, was 118 ms and 420 A* calls. At 7 stops the mean gap fell from 10.5 percent for the greedy tour to 2.4 percent after 2-opt. At 12 stops that gap was 4.8 percent. Eight samples. I left the wobble in the table.

**Source:** `backend/scripts/bench_tour.py`, [`06-phase-5-shopping-route.md`](06-phase-5-shopping-route.md).

---

### Tours — 2-opt from a textbook assumed the way back costs the same

**Likely interview question:** *"How do you stop a heuristic from emitting a nonsense tour?"*

**Short answer (90 seconds, out loud):**
The first 2-opt only replaced the two boundary edges, which is correct when the matrix is symmetric. Ours is not. Escalators are one direction. Tests failed both ways: the greedy trap did not improve, and an already optimal tour got "improved". Repricing the reversed internal edges fixed it. The trap drops from 102 to 4. The optimal tour stays still. Every solver still has to visit each stop once and keep the start. If a stop has no path under the profile, the plan fails and names it. A wheelchair request whose only edge is stairs comes back 422: no wheelchair-accessible route to Island B. We do not skip the store.

**Source:** [`debugging/2026-10-06-directed-2opt.md`](debugging/2026-10-06-directed-2opt.md).

---

### Tours — Wheelchair is a different matrix, not a redraw

**Likely interview question:** *"Does accessible mode change the visit order?"*

**Short answer (90 seconds, out loud):**
The pairs are priced with the same edge filter as a normal route, and only then do we order them. Restroom Ground North, Restroom Level 1, and Nike keep the same order, but the optimized walk goes from 176 m to 204 m. The restroom-to-restroom pair is 112 m versus 180 m. A different list does change order. From the main entrance, Muji then Pages then H&M is 298 m. Wheelchair prefers H&M first, then Muji, then Pages, at 306 m. The five-store demo happened to be identical under normal, wheelchair, and avoid-stairs. I do not pretend every list reshuffles.

**Source:** [`06-phase-5-shopping-route.md`](06-phase-5-shopping-route.md) §9.

