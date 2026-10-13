# 015 — Device-local parking before account sync

**Status:** Accepted
**Date:** 2026-10-09
**Deciders:** MallMind maintainers

## Context

Parking memory is temporary, personal data. The original plan coupled it to JWT authentication and backend CRUD. That makes a small visitor utility depend on account creation, credential security, token refresh, data retention, and deletion policy. None of those concerns is required to remember “P2, Blue B, spot 218” for one visit.

## Options considered

### Authenticated backend record

- Enables cross-device retrieval.
- Introduces credentials, tokens, account recovery, privacy policy, and server-side retention before the core parking flow can ship.

### Anonymous backend record

- Avoids signup.
- Still uploads sensitive location data and needs an identifier, retention policy, abuse controls, and deletion semantics.

### Versioned browser-local record

- Works without an account, is fast, private by default, and has no backend dependency.
- Does not sync across devices and disappears when browser storage is cleared.

## Decision

Ship parking memory as a validated, versioned browser-local record. Reuse the saved mapped entrance as the destination of the existing A* route. Treat authenticated cross-device sync as a later, explicit opt-in capability.

## Why

The local record satisfies the immediate user story with the smallest privacy surface. It also keeps routing authoritative: parking only chooses a destination and never invents a path. Versioning and fail-closed parsing give us a migration boundary if the record evolves.

## Trade-offs

The parking spot is tied to one browser profile. Clearing site data removes it. There is no account history, remote logout, or retrieval from another phone. The UI must state these limits clearly.

## What would change this later

Add backend sync only when users ask for cross-device retrieval or parking history. Before doing so, define the threat model, retention/deletion policy, account recovery, token rotation, rate limits, and explicit consent. Local-only mode should remain available.
