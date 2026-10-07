# 008 — Directed edges; bidirectional walks stored as two rows

**Status:** Accepted
**Date:** 2026-10-06
**Deciders:** Basel

## Context

The mall graph must represent:

- ordinary hallways (walkable both ways)
- one-way escalators
- possible one-way fire stairs
- elevator rides (usually both ways, but wait times can differ by direction later)

A* only needs "the list of outgoing edges from the current node." How we store that list in Postgres is the question.

## Options considered

### Option A — Undirected edges with an `is_bidirectional` flag
- **Pros:** half as many hallway rows.
- **Cons:** every traversal has to synthesise a reverse edge in application code; one-way vs two-way is a special case in A*; asymmetric costs (up-elevator vs down-elevator) cannot be stored on one row without extra columns.

### Option B — Directed edges only; a two-way hallway is two rows `(A→B)` and `(B→A)`
- **Pros:** A* is a uniform "expand outgoing neighbours" loop; one-way is the default; costs can differ by direction; `UNIQUE (from_node_id, to_node_id)` is a simple uniqueness rule; a missing reverse edge is a real, inspectable fact.
- **Cons:** ~2× hallway rows; seed authors (or the generator) must remember to emit both directions.

### Option C — Directed edges in the DB, plus a generator that always mirrors hallway/elevator/stairs unless told not to
- **Pros:** Option B's runtime simplicity, with less chance of a forgotten reverse edge in the seed.
- **Cons:** a little generator complexity. The JSON on disk still stores both rows, so the validator can still see a missing reverse and complain.

## Decision

**Option B in the database, Option C at seed-generation time.** The table stores directed edges. The NOVA Mall generator emits both directions for hallway, elevator, and stairs. Escalators are emitted one way. The validator does **not** auto-repair a missing reverse — it reports it, because a missing reverse might be intentional (a one-way corridor) and silently adding it would hide an authoring bug.

## Why

1. **A* stays boring.** Boring algorithms are easier to test. Special-casing "if bidirectional, also expand reverse" is how off-by-one routing bugs are born.
2. **Escalators are actually one-way.** Modelling the common case as directed means the unusual case is free.
3. **Asymmetric costs later.** An elevator going up may wait longer than one going down. Two rows make that a data change, not a schema change.

## Trade-offs

| We give up | We accept this because |
|---|---|
| Fewer rows | A few hundred extra rows is noise at this scale. |
| Seed files are more verbose | The generator writes them; humans read the validator output. |
| A forgotten reverse edge is a real bug | That is the point — we want to *see* it. |

## What would change this later

- A graph of millions of edges where storage mattered — then a compressed undirected representation plus an in-memory expansion step might win. We are nowhere near that.
- A map editor UI that lets a user draw a corridor once — the editor would still insert two rows.
