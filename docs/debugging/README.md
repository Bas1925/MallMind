# Debugging Journal

A log of **real** bugs encountered during MallMind development, with their investigation and fix.

## Policy

- **One entry per non-trivial bug.** Typos and lint warnings don't count. A bug that cost more than ~15 minutes to find, or whose root cause taught us something, does.
- **Only real bugs.** Nothing invented. If this folder is empty at the end of the project, it was empty for a reason.
- **Written while the context is fresh.** Writing a bug up a week later usually loses the interesting details.

## Why this folder exists

Interview questions about debugging separate candidates sharply. "What's the hardest bug you've debugged?" is answered weakly by *"I don't remember any specific one"* and strongly by *"let me tell you about the one-way edge bug on 2026-10-14 that made all cross-floor routes 40% longer than they should have been."*

This folder is the raw material for those answers.

## Entry format

Each entry is a dated file: `YYYY-MM-DD-short-slug.md`.

```markdown
# <date> — <one-line summary>

**Severity:** low | medium | high | critical
**Time to find:** approximate
**Area:** navigation | search | assistant | auth | infra | …

## Symptom

What did the user (or the test, or the CI run) see?

## Hypothesis path

What did I think the cause was first? What ruled each hypothesis in or out?
This is the most valuable section — it shows the investigation process, not just the answer.

## Root cause

The actual bug. Precise. Code pointer if possible.

## Fix

What was changed. Link the commit or PR.

## Prevention

What test (or lint rule, or type) was added so this specific bug cannot recur silently?

## Lesson

What general lesson, if any, transfers to future work?
```

## Entries

- [`2026-10-05-health-endpoint-missed-connectionrefused.md`](2026-10-05-health-endpoint-missed-connectionrefused.md)
- [`2026-10-05-frontend-cve-surge-on-first-install.md`](2026-10-05-frontend-cve-surge-on-first-install.md)
- [`2026-10-06-docker-engine-needs-virtual-machine-platform.md`](2026-10-06-docker-engine-needs-virtual-machine-platform.md)
- [`2026-10-06-enum-name-vs-value.md`](2026-10-06-enum-name-vs-value.md)
- [`2026-10-06-svg-y-flip-viewbox.md`](2026-10-06-svg-y-flip-viewbox.md)
- [`2026-10-06-cors-origins-json-env.md`](2026-10-06-cors-origins-json-env.md)
- [`2026-10-06-trigram-short-name.md`](2026-10-06-trigram-short-name.md)
- [`2026-10-06-hebrew-definite-article.md`](2026-10-06-hebrew-definite-article.md)
- [`2026-10-07-coffee-ranked-mcdonalds-first.md`](2026-10-07-coffee-ranked-mcdonalds-first.md)
- [`2026-10-07-elevator-ride-split-into-steps.md`](2026-10-07-elevator-ride-split-into-steps.md)
- [`2026-10-07-assistant-language-leaks.md`](2026-10-07-assistant-language-leaks.md)
