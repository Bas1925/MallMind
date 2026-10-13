# Publication and verification — 13 October 2026

Published repository: [Bas1925/MallMind](https://github.com/Bas1925/MallMind), public, with `main` as the default branch. This report records both local preparation and the subsequent [GitHub Actions](https://github.com/Bas1925/MallMind/actions) verification.

## Status

The user authorized creation and publication of the repository linked above. The reviewed project was committed and pushed normally; existing user changes were preserved and no history rewrite was performed. Public application hosting remains unconfigured.

The project is a synthetic mall-navigation prototype. A real mall, real customers, live positioning and a paid model are not prerequisites for demonstrating its algorithms or interaction design.

## Verified on GitHub

The initial publication commit was `5072287`. The first Linux frontend installations exposed two missing peer-dependency records in the npm lockfile. Commit `066c01f` regenerated the lockfile with npm 10.9.9, adding those records without changing any existing package versions. No checks were disabled or relaxed.

| Workflow | Observed result | Evidence |
| --- | --- | --- |
| Backend | Lint/format passed; 126 tests passed, 0 skipped; 76% reported coverage | [Run on `5072287`](https://github.com/Bas1925/MallMind/actions/runs/38414189595) |
| Frontend | Lint, strict types, production build and all 52 component/unit tests passed | [Run on `066c01f`](https://github.com/Bas1925/MallMind/actions/runs/38415220085) |
| Browser journeys | All 20 tests passed across desktop and mobile Chromium emulation, with retries disabled | [Run on `066c01f`](https://github.com/Bas1925/MallMind/actions/runs/38415219977) |
| Production containers | Images built; migrations, seed, startup, page and same-origin API checks passed | [Run on `066c01f`](https://github.com/Bas1925/MallMind/actions/runs/38415220009) |
| Publication safety | Guard tests and source/history checks passed | [Run on `066c01f`](https://github.com/Bas1925/MallMind/actions/runs/38415220360) |

The backend did not rerun for the frontend-lockfile-only change because its workflow uses path filters; its source is unchanged from the successful backend run. The production dependency audit reported **0 known vulnerabilities**. The full install still reported **9 development-tool dependency findings (2 moderate, 7 high)**; these remain a maintenance follow-up, not a claim of a clean full-tree security audit. The backend run also retained the async connection-cancellation warning noted below.

## Completed in this pass

- Corrected production-smoke expectations for the new 33-location seed and checked the service-maze slugs.
- Applied the formatter-only fix in `backend/app/routing/search.py`; backend lint and formatting both pass.
- Added read-only workflow permissions and job time limits, plus a tested publication-safety workflow.
- Added a redacted source/index/history guard for private/generated files and supported credential patterns; ignored private keys and local video output.
- Updated development Compose to same-origin API requests and a no-paid-key/no-model-download default.
- Updated README/case-study measurements for the current graph and added a standalone CV entry, demo guide, and publication checklist.
- Recorded an actual **63.48-second silent demo** at 1440×900 against the real local API/database. The 4.38 MB WebM is in `.validation/mallmind-demo.webm`; it is intentionally not committed or uploaded. The recording script can reproduce it.

## Local preparation checks

| Check | Observed result |
| --- | --- |
| Publication guard tests | 6 passed |
| Source/index/history check | No supported credential patterns or private/generated path findings |
| Backend lint/format | Passed; 101 files formatted |
| Full backend suite, dedicated disposable PostgreSQL database | 126 passed, 0 skipped; 1 async connection-cancellation warning |
| Frontend lint / strict TypeScript | Passed |
| Frontend unit/component suite | 52 passed |
| Real-browser suite on existing production build | 20 passed across desktop/mobile emulation |
| Development and production Compose configuration | Both validated |
| All five workflow YAML structures | Parsed; jobs have read-only contents permission and time limits |
| Current demo map | 3 floors, 33 locations, 110 nodes, 288 directed edges |
| Main Entrance → MUJI | A*: 27 expansions; Dijkstra: 71; both 118 m |
| Canonical five-stop tour | 442.5 m → 382.5 m, saving 13.6% |
| 100×100 synthetic grid | A* and Dijkstra both expand 10,000 nodes |

The backend test database was created separately from the demo database. No demo data was reseeded. The temporary database is retained locally for reproducibility; it is not part of Git.

## Limits and remaining external steps

- The guard is a limited preflight, not a complete secret/security audit. It does not recognize arbitrary passwords, personal information in screenshots, or every credential format.
- The async database warning remains a test-harness follow-up; it was not hidden or counted as a failed test.
- Local Docker configuration validation was not a local container build: Docker's Linux engine was unavailable on this host. The separate GitHub-hosted container build/smoke run above subsequently passed.
- The full development-tool dependency audit is not clean; the passing production-only audit does not cover those development packages.
- Public application hosting, physical-device testing and a publicly uploaded walkthrough video remain unverified. Browser mobile emulation is not a physical-device test.
- Use the real repository link in the CV. Add demo/video URLs only after they are publicly available; localhost is not a public demo.

## Handoff files

- [CV project entry](cv-project-entry.md)
- [90-second demo guide and recorder](demo-walkthrough.md)
- [Publication checklist](github-publication.md)
- [Engineering case study](portfolio-case-study.md)
- [Earlier repair evidence](repair-review-2026-10-13.md)
