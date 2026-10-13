# 07 — Phase 6: Parking memory

**Status:** Implemented and frontend-tested on 2026-10-09.

## Goal

A visitor can record enough information to find a parked car: parking level, zone or spot, an optional note, and the mall entrance used. The saved entrance feeds the existing A* route; parking does not add a second routing system.

## Storage and privacy boundary

The record is stored in browser `localStorage` under the versioned key `mallmind.parking.v1`. It is never sent to the MallMind API. The UI says this before the visitor saves anything.

This is a product decision, not a substitute for authentication. Parking memory is useful immediately, works offline after the app loads, and does not make a visitor create an account for temporary data. Account-backed cross-device sync remains a separate opt-in phase.

## Record contract

The stored object contains:

- schema version and mall slug
- level, zone, spot, and note
- the mapped parking-entrance location id
- an ISO-8601 save timestamp

Level is required. At least a zone or spot is required. Inputs are trimmed, whitespace-normalized, and length-limited before persistence. Reads fail closed: malformed JSON, an unknown schema, invalid fields, or a record belonging to another mall is ignored.

## Map integration

Only locations whose slug contains `parking` and whose map/category type is an entrance are offered as parking entrances. This prevents a store or service containing the word “parking” from becoming a routing anchor.

“Route to car” uses the visitor's selected route origin and the saved entrance as the destination. When no origin is selected, the entrance is set as the destination and the visitor is sent to the Route panel to choose a starting point.

If the entrance disappeared from a newer map, routing is disabled and the visitor is asked to update the saved spot. Stale local data therefore cannot submit an unknown location id to the navigation API.

## Failure handling

Browser storage can be unavailable because of privacy settings, quota limits, or an embedded browser policy. Save and clear operations are caught and reported in the panel. A storage failure never crashes the map.

The main map error screen now also has a retry action. A transient API failure no longer requires a page reload.

## Verification

Vitest covers normalization, persistence, restoration, deletion, malformed data, cross-mall isolation, required fields, the save UI, and the route callback. Strict TypeScript and zero-warning ESLint remain required.

## Deliberately deferred

- accounts, password handling, and token lifecycle
- server-side parking CRUD and cross-device sync
- camera/OCR detection
- indoor positioning inside the garage
- parking reminders and notifications

Those features need their own threat model and product requirements. They are not implied by this local feature.
