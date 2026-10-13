# Dependency maintenance

On 12 October 2026, `npm audit --omit=dev` reported a vulnerable PostCSS 8.4.31 nested under Next.js 15.5.27. The root PostCSS dependency was already pinned to 8.5.29.

The frontend now uses an npm override scoped to Next.js, referencing `$postcss` so both resolve to the same pinned version. The lockfile is regenerated, and compatibility is checked with a clean install, production build, component tests, and browser journeys. This avoids an unrelated major framework migration in the reliability changes.

The audit includes the [PostCSS source-map traversal advisory](https://github.com/advisories/GHSA-r28c-9q8g-f849) and [CSS stringification advisory](https://github.com/advisories/GHSA-qx2v-qp2m-jg93). These advisories do not establish that MallMind itself is exploitable: the app does not expose arbitrary user CSS processing. The dependency fix removes the known vulnerable package from the production tree.

Frontend CI runs `npm audit --omit=dev --audit-level=high`. A clean audit is a point-in-time dependency check, not a full security audit. Re-evaluate the override when upgrading Next.js and remove it once upstream uses an appropriate version.

Development tooling was also updated: TypeScript ESLint 8.71.1 and Vitest 4.1.11. The latter removes the vulnerable worker-pool chain; the migration was checked against the [Vitest 4 guide](https://v4.vitest.dev/guide/migration.html) and the existing suite.

The remaining full-tree audit findings are in build/lint dependencies (9 findings: 7 high, 2 moderate; zero critical). These are not included in the production-only audit. In particular, the braces 3.x stack-exhaustion advisory has no patched 3.x release at review time. A Tailwind/ESLint toolchain migration should be handled separately and validated visually. No claim of an entirely vulnerability-free development tree is made.
