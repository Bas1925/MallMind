# 2026-10-06 — CORS_ORIGINS comma string vs JSON list

**Severity:** low
**Time to find:** ~5 minutes (blocked `uvicorn` before E2E)
**Area:** infra

## Symptom

`CORS_ORIGINS=http://localhost:3000 python -m uvicorn app.main:app` crashed:

`SettingsError: error parsing value for field "cors_origins" from source "EnvSettingsSource"`

(`JSONDecodeError: Expecting value`)

## Hypothesis path

The field already has a `@field_validator` that accepts comma-separated strings. I assumed the env var would hit that validator. It never got there: pydantic-settings treats `list[str]` as JSON and `json.loads` runs first.

## Root cause

Complex env values are decoded as JSON before model validators. A bare URL is not JSON. The default `["http://localhost:3000"]` is fine when the var is unset.

## Fix

Do not set `CORS_ORIGINS` for local uvicorn; the default already allows the Next app. For compose/docs, use JSON: `["http://localhost:3000"]`.

## Prevention

This is documented here so the next local run does not “fix” CORS by pasting a comma list. A follow-up can make the validator run on the raw string (custom source) if operators keep tripping.

## Lesson

Validators on Pydantic models do not wrap pydantic-settings JSON decoding for list/dict env vars.
