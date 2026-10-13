# GitHub publication checklist

Destination: [Bas1925/MallMind](https://github.com/Bas1925/MallMind), public, with `main` as the default branch. Application hosting is separate from publishing source code.

Publish the **mallmind/** repository containing this README, not the parent mallapp folder. Existing user changes remain intact; review the complete diff before the first publication commit.

## Prepared locally

- README with real screenshots, current seed counts, reproducible benchmark claims, demo instructions and explicit simulation boundaries.
- Separate [CV text](cv-project-entry.md) and [recordable walkthrough](demo-walkthrough.md).
- Frontend, backend, real-browser, production-container and publication-safety workflows.
- Ignored environment files, dependencies, build caches, local databases, private-key files and recordings.
- A publication guard that reports high-confidence findings without echoing matched values.

## Before any push

1. Run `node --test scripts/check-publication.test.mjs` and `node scripts/check-publication.mjs --history` from the repository root.
2. Review `git status --short`, `git diff --check`, and the proposed commit. The guard is a supplement to review, not a complete secret or personal-data audit. It does not inspect secrets inside images or identify arbitrary passwords.
3. Confirm the exact destination repository and its visibility. No remote is invented or a new public repository created automatically.
4. Commit the reviewed source and documentation. Do not include `.env`, database files, `.validation/`, `node_modules/`, `.venv/`, or video output. Never force-push to replace unrelated remote history.
5. After the push, check every GitHub Actions result. Fix any failure before adding success badges or claiming remote CI passed.
6. Add the real repository URL and optional demo/video URL to README and the CV. Keep localhost links clearly labeled as local-only.

## Expected GitHub checks

| Workflow | Evidence |
| --- | --- |
| frontend-ci | Lint, strict types, production build, component tests, production dependency audit |
| backend-ci | Formatting/lint plus PostgreSQL-backed tests with missing databases treated as failures |
| e2e-navigation | Desktop/mobile browser journeys against a seeded API |
| production-containers | Build isolated containers, run migrations/seed, verify the page and same-origin API |
| publication-safety | Check source/index/history for private paths and supported credential patterns |

The database created inside CI is disposable. Do not point integration tests or forced seeding at an existing personal or production database. The production smoke job's volume deletion applies only to its isolated CI project.

See [publication-readiness.md](publication-readiness.md) for what was actually checked locally and what still needs the destination repository.
