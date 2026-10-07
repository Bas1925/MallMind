# 001 — Modular monolith over microservices

**Status:** Accepted
**Date:** 2026-10-05
**Deciders:** Basel

## Context

MallMind has roughly four cohesive subsystems: **navigation**, **search**, **AI assistant**, and **user data (auth + parking)**. Each has distinct responsibilities but they share the same domain model (locations, map nodes, users) and the same database.

Constraints:

- Single developer, part-time schedule
- Portfolio project — the goal is to demonstrate thinking, not to serve millions of users
- Must be understandable end-to-end in an interview conversation
- Must be deployable to one small cloud instance

What we're optimizing for: **time-to-correctness and explainability**, not independent scalability.

## Options considered

### Option A — Microservices (one service per subsystem)
- **Pros:** independent deploys and scaling; language-per-service freedom; teams can own services independently; fault isolation.
- **Cons:** need service discovery, inter-service auth, distributed tracing, and a message bus or careful HTTP contracts; shared models become duplicated schemas; a single database transaction across services becomes a distributed-transaction problem (sagas, 2PC, or eventual consistency); significantly more infrastructure to maintain; small changes often touch 2–3 services and 2–3 CI pipelines.

### Option B — Single-file monolith (one `main.py`, no module structure)
- **Pros:** fastest to start; zero abstraction tax.
- **Cons:** doesn't scale beyond a few hundred lines; business logic mixes with HTTP handling; nothing is independently testable; shows the wrong signal in a portfolio ("no architectural thinking").

### Option C — Modular monolith (one process, strong internal module boundaries)
- **Pros:** one deploy, one DB, one transaction boundary — zero distributed-system complexity; strict internal layering (router → service → repository → algorithm) gives per-module testability; cheap to extract a module into a service later if real load justifies it; perfectly matches the single-developer context.
- **Cons:** cannot scale a single subsystem independently; one bug can crash the whole process; a careless developer can leak coupling across module boundaries that look like microservices wouldn't allow.

## Decision

**Option C — Modular monolith.** The backend will be a single FastAPI application organised into clearly-separated modules (`navigation`, `search`, `assistant`, `parking`, `auth`), each layered as `routers → services → repositories → algorithms`. All modules share one PostgreSQL database.

## Why

1. **Scope match.** We have one developer. Microservices optimize for organisational scale (independent teams); we don't have teams.
2. **Operational cost.** The real cost of microservices is not writing them, it's operating them — service discovery, inter-service auth, log aggregation, distributed tracing. For a portfolio project, this cost dwarfs the benefit.
3. **Interview optics.** "I chose a monolith because the system doesn't need distributed consistency, service discovery, or inter-service latency" is a more honest and senior answer than "I used Kubernetes because it was cool."
4. **Extraction path is cheap.** With clean module boundaries, extracting (for example) the navigation service into a separate deployable is a few days of work. We don't pay the cost until the benefit is real.
5. **Transactional simplicity.** A single DB means we never deal with distributed transactions, which are an entire category of problems we don't need to solve.

## Trade-offs

| We give up | We accept this because |
|---|---|
| Independent scaling of subsystems | Nothing in MallMind has an obviously different scale profile; routing is CPU-bound in-process, search is DB-bound, assistant is LLM-bound — but none at a volume that justifies splitting. |
| Fault isolation between modules | A critical bug in one module takes the whole process down. Mitigated by good test coverage on hot paths (algorithms especially). |
| Independent tech-stack choice per module | We're committed to Python/FastAPI for everything. That's a feature, not a bug, at this size. |
| Freedom to use different databases per bounded context | One DB simplifies ops; we lose some fine-grained optimisation. |

## What would change this later

Specific triggers that would make us reopen this ADR:

- **Scale divergence:** navigation serves 10× more RPS than the assistant for a sustained period; worth extracting navigation to scale it separately.
- **Team growth:** more than ~3 engineers working on the backend simultaneously, with frequent merge conflicts.
- **Different runtime needs:** the assistant genuinely needs long-running GPU workloads that don't belong next to a request-handling API.
- **Reliability isolation:** we need the ability to deploy and roll back `navigation` without affecting `assistant`.

In the absence of these triggers, the monolith stays.

## Related

- See [`002-astar-with-dijkstra-baseline.md`](002-astar-with-dijkstra-baseline.md) for the navigation algorithm choice.
- See [`003-postgresql-with-pgvector.md`](003-postgresql-with-pgvector.md) for the "one database" choice.
