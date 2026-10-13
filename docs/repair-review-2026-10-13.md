# Local repair and portfolio review — 13 October 2026

## Changes

- Recovered the unresponsive frontend on port 3000 by restarting its verified Next.js process. Before recovery, both HTTP and browser navigation timed out while the backend and database stayed healthy. Restarting resolved the symptom; the exact cause of the old process hang was not established.
- Built and started production mode from the original checkout, not the earlier review copy. The current local preview is http://localhost:3000/#stores.
- Merged ten real brand logos into store cards, details, and the map sidebar. Assets are served locally, preserve aspect ratios, and fall back to readable store names. Fictional stores retain their own text/initial identities. See [asset sources and rights](brand-assets.md).
- Preserved the existing A*, Dijkstra, BFS/DFS, search-maze, and route-animation changes. No backend source or database records were changed by this repair.
- Added logo component/browser regression checks and made the screenshot workflow wait for visible directory logos before capture.

## Fresh verification

| Check | Result |
| --- | --- |
| Frontend unit/component tests | 52 passed in 12 files |
| Strict TypeScript | Passed |
| Production build, including lint/type validation | Passed; home first-load JS reported as 136 kB |
| End-to-end tests against production mode and the live API | 20 passed: 10 scenarios on desktop and mobile Edge/Chromium |
| Pure routing and search-maze tests | 12 passed; no database reseed |
| Same-origin service health | status=ok, db=ok |
| Directory widths 320, 390, 768, 1440 px | HTTP 200, no horizontal overflow or uncaught page errors during the checked load |
| Screenshots | Desktop directory/map and mobile directory/route inspected; capture completed for all seven documented views |

Browser coverage includes all ten local logo loads, a detail-dialog logo, map-sidebar logos, combined filtering/reset, Escape/focus restoration, real directions, visit-plan invalidation, floor handoff, browser Back, keyboard search, parking persistence, Arabic responses, and unknown-store refusal. Mobile checks are emulation, not physical-phone tests.

The full database integration suite, dependency audit, container smoke test, and remote CI were not rerun in this repair. Historical results in [the earlier release review](release-review.md) are not fresh verification of the new backend changes. No public deployment or full accessibility/security audit is claimed.

## Local running mode

The preview uses `npm run start` with the verified build. For source editing, stop that frontend process and run `npm run dev` from `frontend/`. Do not run development and a production build simultaneously against the same `.next` directory. Rebuild before using production mode after source changes.

If the local frontend stops responding again, check the terminal output and `/api/v1/health`, then restart only this project's frontend process. Preserve the database and source files; do not force-reseed or delete project data to recover a hung preview.

## Portfolio assessment

Subjective assessment: **8.5/10 as a junior/full-stack CV project in its current local state**. The distinctive directory, functioning API-backed routes, trip optimization, accessible-route options, parking memory, and regression coverage give it substance beyond a static mockup.

The next evidence needed for a stronger public portfolio is a hosted HTTPS demo, successful remote CI/container checks, a physical-phone/usability pass, and real repository/demo links in the CV. The synthetic mall and template-based assistant must remain clearly described as demo capabilities, not live indoor navigation or a verified chat-model deployment.
