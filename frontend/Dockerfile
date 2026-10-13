# syntax=docker/dockerfile:1.7
# =============================================================================
# MallMind frontend — Next.js dev container
# =============================================================================
# Dev-friendly image:
#   - installs deps once at build time
#   - src is bind-mounted by compose for hot reload
#   - node_modules and .next are kept inside the container via anonymous
#     volumes (declared in compose) to avoid platform ABI mismatches
#
# Phase 9 (production) will use a multi-stage build with `next build` +
# `output: "standalone"` for a slim runtime image.
# =============================================================================

FROM node:22-alpine
WORKDIR /app

# Install deps against the lockfile for reproducibility. If the lockfile
# doesn't exist yet (first `docker compose up`), fall back to `npm install`
# which will generate one.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]
