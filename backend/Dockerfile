# syntax=docker/dockerfile:1.7
# =============================================================================
# MallMind backend — Python 3.12-slim, non-root, with HEALTHCHECK
# =============================================================================
# Dev-friendly image used by docker-compose:
#   - installs runtime deps only (dev deps live outside the image)
#   - source is volume-mounted by compose for hot reload
#   - CMD runs uvicorn with --reload
#
# For production (Phase 9) we'll split this into a multi-stage build without
# --reload and with a frozen requirements set.
# =============================================================================

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install only prod deps declared in pyproject.toml.
# Copy the package sources before `pip install .` so setuptools can find `app`.
COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic
RUN pip install --upgrade pip && pip install .

# Drop privileges.
RUN useradd --create-home --uid 1000 app && chown -R app:app /app
USER app

EXPOSE 8000

# Container-level health check hits our own /health endpoint.
# Returns healthy iff the backend reaches Postgres (endpoint returns 503 otherwise).
# urllib.request.urlopen raises on non-2xx, so a 503 correctly flips us to unhealthy.
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health', timeout=3)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
