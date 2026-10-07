# 004 — Use FastAPI for the backend

**Status:** Accepted
**Date:** 2026-10-05
**Deciders:** Basel

## Context

The MallMind backend needs to:

- Serve JSON over HTTP (REST).
- Validate requests at the boundary (reject malformed input with a clear error).
- Make outbound network calls to an LLM provider (ideally async so request handlers don't block).
- Produce an OpenAPI schema so the frontend can generate typed clients.
- Be easy for a single developer to reason about end-to-end.

The alternatives are mature Python web frameworks that each make different trade-offs.

## Options considered

### Option A — Flask
- **Pros:** minimal, well-known, huge ecosystem; easy to learn.
- **Cons:** validation and serialization are not built in (need Marshmallow or similar); no first-class async support (ASGI available via Quart but that's a different project); OpenAPI generation needs an extra library and feels bolted on.

### Option B — Django + Django REST Framework
- **Pros:** batteries included (ORM, admin, auth); production-grade for CRUD apps; strong ecosystem.
- **Cons:** heavy for the shape of this project; async support is improving but still awkward in handlers that depend on DRF serializers; the admin we don't need, the migrations we'd replace with Alembic for pgvector reasons, and the full ORM we'd use selectively — most of Django's value isn't paid off here.

### Option C — FastAPI (on top of Starlette)
- **Pros:** request/response validation via Pydantic at zero extra cost; auto-generated OpenAPI + interactive Swagger UI; async-native handlers; dependency-injection system that fits naturally with DB session scoping; strong typing throughout; modern and well-maintained.
- **Cons:** smaller ecosystem than Django; no built-in admin; dependency-injection system is powerful but can be misused to hide business logic in request lifecycles.

### Option D — Bare Starlette or Litestar
- **Pros:** Starlette is what FastAPI is built on; Litestar is a newer FastAPI-alike with some nice ergonomic choices.
- **Cons:** Starlette alone means we re-invent the Pydantic integration that FastAPI gives us for free. Litestar is less proven in the ecosystem and less well-known in interviews.

## Decision

**Option C — FastAPI.**

## Why

1. **Pydantic validation at the boundary.** Request bodies, query params, and responses are typed and validated. Bad input produces a well-structured 422 error automatically; the handler receives already-validated typed objects. This eliminates an entire category of bugs that other frameworks require ceremony to prevent.
2. **Auto-generated OpenAPI.** The frontend can generate typed TypeScript clients from the spec. API drift between frontend and backend becomes a build failure instead of a runtime bug.
3. **Async handlers.** The AI assistant calls an external LLM — a request that can take 1–3 seconds. Async handlers let the server keep processing other requests during that wait. In a sync framework the worker would block.
4. **Dependency injection fits our layering.** Our router→service→repository pattern maps naturally to FastAPI's `Depends()` system: the router declares what it needs (a DB session, a service), FastAPI wires it up, and the handler stays small.
5. **Interview optics.** FastAPI is widely known in modern Python shops. Explaining *"I chose FastAPI because validation and OpenAPI are first-class, and I needed async for LLM calls"* is a credible, specific answer.

## Trade-offs

| We give up | We accept this because |
|---|---|
| Django's batteries (admin, auth, templating) | We don't need any of them for the MVP. If we did, Django Admin for a graph-based app would be awkward anyway. |
| Flask's "a single file is enough" simplicity | We're building a real backend, not a demo; the extra structure pays for itself immediately. |
| A smaller stdlib of third-party packages (compared to Django) | FastAPI + SQLAlchemy + Alembic + Pydantic covers everything we need. |

## What would change this later

- **Need built-in admin + heavy CRUD UI:** Django would start to look attractive. We'd probably still keep FastAPI for the API surface and run Django Admin separately — but that's a different architecture.
- **Need sync-only integrations:** none expected; this is unlikely.
- **Framework maintenance deteriorates:** FastAPI is well-maintained today. If that changed, Litestar or bare Starlette are drop-in-ish alternatives.

## Related

- [`001-modular-monolith.md`](001-modular-monolith.md) — the architectural layer FastAPI sits inside.
- [`003-postgresql-with-pgvector.md`](003-postgresql-with-pgvector.md) — database choice; SQLAlchemy async works cleanly with FastAPI async handlers.
