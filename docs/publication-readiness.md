# Publication preparation — 13 October 2026

Publication destination: [Bas1925/MallMind](https://github.com/Bas1925/MallMind). This report preserves the pre-push preparation evidence below; [GitHub Actions](https://github.com/Bas1925/MallMind/actions) is the source for subsequent remote verification.

## Status

At the time of the preparation review, the project was local-only and the destination was still required. The user subsequently authorized creation and publication of the repository linked above. Public application hosting remains unconfigured. Existing user changes were preserved; no history rewrite was performed.

The project is a synthetic mall-navigation prototype. A real mall, real customers, live positioning and a paid model are not prerequisites for demonstrating its algorithms or interaction design.

## Completed in this pass

- Corrected production-smoke expectations for the new 33-location seed and checked the service-maze slugs.
- Applied the formatter-only fix in `backend/app/routing/search.py`; backend lint and formatting both pass.
- Added read-only workflow permissions and job time limits, plus a tested publication-safety workflow.
- Added a redacted source/index/history guard for private/generated files and supported credential patterns; ignored private keys and local video output.
- Updated development Compose to same-origin API requests and a no-paid-key/no-model-download default.
- Updated README/case-study measurements for the current graph and added a standalone CV entry, demo guide, and publication checklist.
- Recorded an actual **63.48-second silent demo** at 1440×900 against the real local API/database. The 4.38 MB WebM is in `.validation/mallmind-demo.webm`; it is intentionally not committed or uploaded. The recording script can reproduce it.

## Fresh checks

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
- The earlier same-day production build is unchanged at the UI-source level in this pass. The new recording command is tooling only. No new production build or dependency audit is claimed here.
- Docker's Linux engine is not running on this host, so configuration validation is not a container build/smoke success. Run the configured production smoke workflow after publication.
- GitHub-hosted Actions, public hosting, physical-device testing and an uploaded video link remain unverified. There are no fabricated success badges or live URLs.
- The destination repository is now specified. Complete the normal non-force push and inspect actual workflow results; use the real repository link in the CV and add demo/video URLs only after they are publicly available.

## Handoff files

- [CV project entry](cv-project-entry.md)
- [90-second demo guide and recorder](demo-walkthrough.md)
- [Publication checklist](github-publication.md)
- [Engineering case study](portfolio-case-study.md)
- [Earlier repair evidence](repair-review-2026-10-13.md)
