# Architecture Decision Records (ADRs)

This folder holds the **why** behind MallMind's architecture. Code shows *what* we built; ADRs show *why* we built it that way, *what else we considered*, and *what would make us change our minds*.

## When to write an ADR

Write one for any decision that:

- is hard or expensive to reverse
- affects multiple parts of the system
- a future engineer (or an interviewer) would reasonably ask "why?" about
- has at least two sensible options

Do **not** write ADRs for small reversible decisions (variable names, which lint rule to enable, etc.).

## Format

Every ADR follows the same shape. Short. One screen if possible.

```markdown
# NNN — Short decision title

**Status:** Proposed | Accepted | Superseded by NNN | Deprecated
**Date:** YYYY-MM-DD
**Deciders:** names

## Context

What problem are we solving? What constraints are in play? What are we trying to optimize for?

## Options considered

### Option A — <name>
- Pros
- Cons

### Option B — <name>
- Pros
- Cons

(etc.)

## Decision

The chosen option, in one sentence.

## Why

The reasoning. Prefer concrete over abstract. If a benchmark or a user story drove it, cite it.

## Trade-offs

The real cost of this decision. What are we giving up?

## What would change this later

Specific triggers that would force us to revisit. "If X happens, we should reopen this ADR."
```

## Numbering

ADRs are numbered sequentially starting at 001. Numbers are never reused. If an ADR is superseded, the new one gets a new number and the old one is marked `Superseded by NNN`.

## Current ADRs

| # | Title | Status |
|---|---|---|
| [001](001-modular-monolith.md) | Modular monolith over microservices | Accepted |
| [002](002-astar-with-dijkstra-baseline.md) | A* for production, Dijkstra as baseline | Accepted |
| [003](003-postgresql-with-pgvector.md) | PostgreSQL + pgvector for data and embeddings | Accepted |
| [004](004-use-fastapi.md) | Use FastAPI for the backend | Accepted |
| [005](005-pip-tools-for-locking.md) | pip-tools for Python dependency locking | Accepted |
| [006](006-alembic-migration-strategy.md) | Alembic is the only schema-management strategy | Accepted |
| [007](007-floor-local-coordinates.md) | Floor-local Cartesian coordinates for graph nodes | Accepted |
| [008](008-directed-graph-edges.md) | Directed edges; bidirectional walks stored as two rows | Accepted |
| [009](009-astar-heuristic-strategy.md) | Euclidean A* heuristic; no vertical bonus | Accepted |
| [010](010-svg-for-indoor-map-rendering.md) | SVG for indoor map rendering | Accepted |
| [011](011-hybrid-lexical-and-vector-search.md) | Hybrid lexical search with a vector fallback | Accepted |
| [012](012-embedding-provider-abstraction.md) | One embedding provider, local by default | Accepted |
| [013](013-tool-first-mall-assistant.md) | Assistant calls tools; the model only phrases | Accepted |
| [014](014-shopping-route-optimization-strategy.md) | Open tour: Held-Karp through 12 stops, then NN + 2-opt | Accepted |
| [015](015-device-local-parking-before-auth.md) | Device-local parking before account sync | Accepted |
