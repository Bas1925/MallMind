# Deployment and verification

## Public release status

Production configuration is prepared. No public domain, hosting account, or GitHub remote is configured by this change. Publish only after the container smoke test and hosted checks below pass. Local production-mode browser tests exercise the real API and PostgreSQL; they do not prove a hosted deployment.

## Development with Docker

Run from the repository root, which contains `frontend/` and `backend/`:

```sh
docker compose up -d --build postgres backend
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
docker compose up -d --build frontend
```

The seed refuses to replace an existing mall. Do not add `--force` to normal startup. Open http://localhost:3000. Schema migrations and seed data are required; starting containers alone does not create a usable map.

## Production

Copy the values below into an untracked `.env.production`, substituting a real HTTPS domain and strong password. Use a URL-encoded password inside the database URL if it contains reserved characters.

```dotenv
POSTGRES_PASSWORD=REPLACE_WITH_A_STRONG_PASSWORD
DATABASE_URL=postgresql+asyncpg://mallmind:REPLACE_WITH_URL_ENCODED_PASSWORD@postgres:5432/mallmind
SITE_URL=https://YOUR_DOMAIN
FRONTEND_PORT=3000
EMBEDDING_PROVIDER=none
```

The baseline runs lexical search and database-grounded multilingual template answers without a paid API. Semantic search and a live chat model are separate configuration choices, not implied by this deployment.

```sh
docker compose --env-file .env.production -f compose.production.yml config --quiet
docker compose --env-file .env.production -f compose.production.yml build
docker compose --env-file .env.production -f compose.production.yml up -d postgres
docker compose --env-file .env.production -f compose.production.yml run --rm backend alembic upgrade head
# First deployment only:
docker compose --env-file .env.production -f compose.production.yml run --rm backend python -m app.seed
docker compose --env-file .env.production -f compose.production.yml up -d
```

Use an HTTPS reverse proxy on the host for `127.0.0.1:3000`. PostgreSQL and the API have no published ports. The frontend sends same-origin `/api/*` requests; Next.js forwards them internally to the API. `SITE_URL` and proxy configuration are build-time values, so rebuild when they change. Frontend runs as the Node user and backend runs as an unprivileged application user.

After deployment:

- Confirm `https://YOUR_DOMAIN/api/v1/health` reports a healthy database.
- Load the map, request a wheelchair route from Main Entrance to Apple, and switch floors.
- Optimize a trip, edit a stop, and verify the old route is removed.
- Save a parking spot, refresh, verify it persists, then clear it.
- Ask for Nike in Arabic and an unknown store in English.
- Check the site on a real phone and verify its link preview uses the public domain.
- Attach the URL and successful GitHub Actions run to the README.

Back up the named PostgreSQL volume before upgrades. Do not delete the volume or run forced seeds against a database with data you need.

## Local setup without Docker

Use Node.js 22 and Python 3.12 or newer. Install PostgreSQL 16 with pgvector and pg_trgm, create a development database, then:

```sh
cd backend
python -m venv .venv
# Activate .venv for your shell, then:
pip install -r requirements-dev-lock.txt
pip install -e . --no-deps
```

Set `DATABASE_URL` to the development database and `EMBEDDING_PROVIDER=none`. In PowerShell use `$env:DATABASE_URL='...'`; in bash use `export DATABASE_URL='...'`. Create the extensions using a database administrator, run `alembic upgrade head` and `python -m app.seed`, then `uvicorn app.main:app --host 127.0.0.1 --port 8000`.

In a second terminal, run `npm ci` and `npm run dev` from `frontend/`. The default proxy targets port 8000; no public API URL is needed.

## Repeatable verification

**Use a dedicated disposable test database. Integration tests intentionally replace the NOVA seed. Never point the test suite at your deployed or personal database.**

Set `DATABASE_URL` to that test database and `REQUIRE_DATABASE_TESTS=1` before running:

```sh
cd backend
ruff check .
ruff format --check .
pytest -q
python scripts/bench_routing.py
python scripts/bench_tour.py
```

The required-database flag makes an unavailable database a failure instead of a green run with skipped integration tests. GitHub Actions sets it automatically.

For the frontend:

```sh
cd frontend
npm ci
npm run lint
npm run typecheck
npm test
npm run build
npx playwright install chromium
npm run e2e
```

Browser tests need the seeded API running on port 8000. They run desktop Chromium and mobile Chromium emulation. Set `CI=1` to test the production build; otherwise the runner starts the development server. An installed Edge browser can be used with `PW_CHANNEL=msedge`. Traces and screenshots are retained on failure; CI uploads the report.

Set `NEXT_STANDALONE=1` only when building the standalone container artifact. Ordinary local builds avoid Windows symlink restrictions. Keep working copies outside OneDrive if its file synchronization causes `readlink EINVAL` during Next.js builds.
