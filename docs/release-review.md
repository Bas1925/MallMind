# Portfolio release review — 12 October 2026

Latest targeted recheck: [13 October repair and portfolio review](repair-review-2026-10-13.md). The results below are historical; use that follow-up for the current frontend/logo verification.

## Completed

- Rebuilt the entry experience as a responsive store directory with an original SVG mall illustration, combined search/category/floor filters, sorting, and accessible store detail dialogs.
- Connected directory selections to the real map and routing API; shared visit stops persist while switching between browsing and visitor tools.
- Corrected all GitHub Actions paths for this repository's actual root.
- Added a production Compose stack, non-root frontend image, same-origin API proxy, and container smoke workflow.
- Fixed stale route, search, trip-plan, and assistant responses; added regression coverage.
- Added keyboard search, a skip link, clear-route action, branded icon, and social preview.
- Refreshed desktop/mobile screenshots from the production build.
- Replaced the long README with a concise portfolio overview; preserved the original notes.
- Added deployment instructions, reproducible measurements, interview demo script, and CV wording.
- Removed the vulnerable nested PostCSS version from production dependencies and updated test/lint tooling.

## Verified locally

| Check | Result |
|---|---|
| Backend lint and formatting | Passed |
| Backend tests with required real PostgreSQL | **123 passed, 0 skipped** |
| Frontend lint and strict TypeScript | Passed |
| Clean dependency installation in original project | Passed after repairing transitive WASM dependency lock metadata |
| Frontend component/unit tests | **38 passed** |
| Production build | Passed; home-page first-load JS reported as 128 kB |
| Real-browser scenarios | **18 passed**: 9 scenarios × desktop and mobile Chromium emulation |
| Production npm dependency audit | **0 known vulnerabilities reported** |
| Production Compose configuration | Validated |
| Screenshots | Captured and visually inspected |

Environment: Windows, Node.js 24.12.0, Python 3.12.0, isolated PostgreSQL 16 with pgvector/pg_trgm, Next.js production server, and installed Edge (Chromium). Browser tests used the real FastAPI service and database; no route API mocks were used. Mobile emulation is not a physical-device test. CI targets Node.js 22 and Python 3.12.

Browser scenarios cover same-floor and wheelchair cross-floor routing, floor switching, keyboard search and horizontal overflow, edited trip plans, parking persistence/clearing, Arabic responses, and unknown-store refusal. The backend suite emitted one asynchronous connection-cancellation runtime warning; no tests failed. That warning remains a test-harness follow-up.

The directory redesign additionally covers combined filters and reset, native dialog Escape/focus restoration, real directions from a store detail, shared visit stops and stale-plan invalidation, and browser Back preserving search filters. Manual viewport checks at 320, 390, 768, and 1440 px found no horizontal overflow; the checked production browser journey emitted no uncaught page errors. This is not a full accessibility audit. No backend or dependency changes were needed for this redesign; the backend and dependency results above are retained from the earlier review on the same date.

The home illustration and store typographic cards are original code-native artwork. Store labels come from the synthetic seed; the UI does not invent opening hours, promotions, or a relationship with the real reference mall. Visit selections persist during the current browsing session, not after a reload.

The review ran from a copy outside OneDrive because the original folder's reparse points blocked patching and caused Next.js cache read errors. Reviewed source files were copied back without committing unrelated existing changes. Original versions of replaced files were backed up in the local review workspace.

## Re-measured benchmark evidence

- Main Entrance → MUJI: equal 118 m route cost; A* expands 27 nodes versus Dijkstra's 70.
- Canonical five-stop shopping route: 442.5 m → 382.5 m; saves 60 m / 13.6%.
- 20-stop tour: mean 81.3 ms across 8 local samples, 420 A* pair calculations per request.
- Opposite corners of a 100×100 grid: both algorithms expand every node.

These measurements describe the synthetic demo data and local environment. They are not user-study outcomes, throughput guarantees, or hosted response-time measurements.

## Remaining release work

1. Connect the intended GitHub repository, commit the reviewed changes, and run the workflows on GitHub. No remote CI success is claimed.
2. Run the production-container smoke job. The local Docker Linux engine is unavailable; only Compose configuration and native production execution were verified here.
3. Choose hosting and a public domain, configure `SITE_URL` and database credentials, deploy, and repeat the hosted checks in [deployment.md](deployment.md).
4. Add the actual live-demo/repository links to the README and CV.
5. Test with a few people unfamiliar with the app and on a physical phone before claiming usability results.

No public deployment, account sync, live indoor positioning, surveyed mall maps, or live chat-model verification is claimed. The assistant baseline uses lexical retrieval and multilingual templates; optional semantic/model providers need separate configuration and verification.

The full development dependency audit still reports 9 findings (7 high, 2 moderate), while the production-only tree reports zero. See [dependency maintenance](dependency-maintenance.md) for scope and follow-up. No full security or accessibility certification is implied.
