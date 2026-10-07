# 005 — pip-tools for Python dependency locking

**Status:** Accepted
**Date:** 2026-10-05
**Deciders:** Basel

## Context

Phase 0b verification turned up a security problem on the frontend: the first `npm install` surfaced 10 CVEs including a Next.js critical, because floating version ranges had drifted away from what I'd written against. The same category of problem applies to Python: pinned ranges in `pyproject.toml` don't lock *transitive* versions, so `pip install` can produce different dependency graphs over time or between machines.

For a project that will be rebuilt in CI, Docker, and on contributor machines, we need **deterministic installs**.

Constraints:

- Keep `pyproject.toml` as the single source of truth for *declared* dependencies.
- Don't swap the installer. `pip` stays.
- Don't introduce a parallel ecosystem (poetry, pdm, uv) for a project this size.
- Lockfile must be human-readable and diff-friendly.
- Must be hashable (nice-to-have for strongest reproducibility; not required for Phase 0b).

## Options considered

### Option A — No lockfile; rely on ranges in `pyproject.toml`
- **Pros:** zero tooling.
- **Cons:** every rebuild can resolve differently; "works on my machine" is a question of time of day.

### Option B — `pip freeze > requirements.txt` after a fresh install
- **Pros:** no new tool.
- **Cons:** captures the state of the current environment, including globally-installed junk; not driven from `pyproject.toml`; no concept of prod vs dev extras.

### Option C — pip-tools (`pip-compile` + `pip-sync`)
- **Pros:** generates a lockfile *from `pyproject.toml`*; supports extras (`--extra=dev`) so we get separate prod and dev locks; output is a plain `requirements*.txt` that `pip install -r` consumes directly — no new installer; well-maintained, part of the pip ecosystem.
- **Cons:** adds a dev-time tool (`pip-tools`); the lockfile is tied to the Python version it was generated under (minor).

### Option D — Switch to Poetry / PDM / uv
- **Pros:** these projects do locking natively.
- **Cons:** each one introduces a new installer, a new file format, a new mental model, and reconfigured CI. Overkill for a single-service monolith. The user explicitly asked not to introduce another package manager.

## Decision

**Option C — pip-tools.**

Two lockfiles live in `backend/`:

- `requirements-lock.txt` — pinned transitive closure of production deps only
- `requirements-dev-lock.txt` — pinned transitive closure including the `dev` extra (ruff, pytest, etc.)

Both are **generated** from `pyproject.toml`; `pyproject.toml` stays the source of truth. CI installs with `pip install -r requirements-dev-lock.txt` for determinism.

## Why

1. **One source of truth.** Dependency *declarations* live in `pyproject.toml` with meaningful version ranges. Dependency *resolution* is captured in the lockfile. These two files have different jobs and change for different reasons.
2. **No new installer.** `pip` still installs. `pip-compile` is just a resolver that writes a text file. Nothing changes about how packages get into the environment.
3. **Extras support.** `--extra=dev` cleanly separates prod from dev lock. CI uses the dev lock; a slim Docker image for prod would use the prod lock.
4. **Diffable.** The lockfile is sorted, commented with the "via" chain, and plain text. A dependency bump shows up as a readable diff in review.
5. **Honest answer in interviews.** "I use pip-tools because I want deterministic installs without introducing a new installer" is a specific, defensible answer. "I use Poetry because everyone else does" isn't.

## Trade-offs

| We give up | We accept this because |
|---|---|
| A single `pip install` without regeneration ever | Running `pip-compile` is a one-command regeneration whenever `pyproject.toml` changes. |
| Hashed lockfiles with `--generate-hashes` (strongest reproducibility) | Not yet needed; the extra noise in the lockfile isn't worth it for Phase 0b. Easy to add later. |
| Automatic dep updates | We update deliberately: edit `pyproject.toml`, run `pip-compile`, review the diff. This is a feature, not a bug. |
| Lockfile is tied to the Python version it was generated under | We generate under 3.12 (same version CI and Docker use); CI will catch any mismatch. |

## Regeneration workflow

```bash
cd backend
pip install pip-tools
pip-compile --strip-extras pyproject.toml -o requirements-lock.txt
pip-compile --strip-extras --extra=dev pyproject.toml -o requirements-dev-lock.txt
```

Both files should be committed.

## What would change this later

- **Need for cryptographic reproducibility** (supply-chain assurance): switch to `pip-compile --generate-hashes`.
- **Multiple Python versions supported in production:** generate per-version lockfiles or move to a tool with native cross-version resolution (uv).
- **Team adopts Poetry or uv elsewhere:** reconsider for consistency.

## Related

- [`004-use-fastapi.md`](004-use-fastapi.md) — the backend install surface we're locking.
- [`docs/debugging/2026-10-05-frontend-cve-surge-on-first-install.md`](../debugging/2026-10-05-frontend-cve-surge-on-first-install.md) — the parallel frontend story that motivated this.
