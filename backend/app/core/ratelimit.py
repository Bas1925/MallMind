"""Single-process sliding window. Not shared across machines.

MallMind is one API process (ADR-001). A Redis limiter would be a second
dependency for a demo that has one user at a time. If we ever run more than
one worker, this limit becomes per-worker and should move.
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse

_hits: dict[str, list[float]] = defaultdict(list)


def enforce_rate_limit(
    request: Request,
    *,
    scope: str,
    max_calls: int,
    window_seconds: float,
) -> JSONResponse | None:
    host = request.client.host if request.client is not None else "unknown"
    key = f"{scope}:{host}"
    now = time.monotonic()
    recent = [stamp for stamp in _hits[key] if now - stamp < window_seconds]
    if len(recent) >= max_calls:
        _hits[key] = recent
        return JSONResponse(
            status_code=429,
            content={"code": "rate_limited", "message": "too many requests"},
        )
    recent.append(now)
    _hits[key] = recent
    return None


def reset_rate_limits_for_tests() -> None:
    _hits.clear()
