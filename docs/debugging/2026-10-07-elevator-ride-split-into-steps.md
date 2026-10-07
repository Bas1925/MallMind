# 2026-10-07 — One elevator ride printed as two steps

**Severity:** low
**Time to find:** minutes, seen in the route panel
**Area:** navigation

## Symptom

Main Entrance → MUJI (Level 2), wheelchair profile:

```
1 Walk 48 m
2 Take the elevator to floor 1
3 Take the elevator to floor 2
4 Walk 70 m
5 Arrive at MUJI
```

The route header said "Ground Floor → Level 1 → Level 2". The steps said "floor 1", a name the UI never uses.

## Hypothesis path

The route itself was right: 118 m, same cost as Dijkstra. So this was presentation only. `instructions_for` folds consecutive hallway edges into one "Walk N m", but emitted one line per vertical edge. The elevator shaft is modelled as one edge per floor gap (ADR-008), so a two-floor ride is two edges.

## Root cause

Hallways were merged; vertical edges were not. The floor text used `floor_level` because `MallGraph` had no floor names.

## Fix

Consecutive vertical edges of the same type merge into one step described by where the ride ends. `MallGraph` gains `floor_names` (level → name), filled from the `floors` table and from the seed, so the step reads "Take the elevator to Level 2". Graphs without names (synthetic test graphs) fall back to "floor N".

## Prevention

`test_one_elevator_ride_across_two_floors_is_one_step` routes the NOVA case under the wheelchair profile and asserts exactly one elevator step.

## Lesson

The graph models how the building is built. Instructions model what a person does. One edge per floor gap is correct for routing and wrong as a sentence.
