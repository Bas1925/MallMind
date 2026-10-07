# 2026-10-05 — Health endpoint 500s instead of 503 when Postgres is unreachable

**Severity:** medium
**Time to find:** ~10 minutes (caught by the first-ever pytest run against a scaffold)
**Area:** backend / observability

## Symptom

During Phase 0b validation, I installed the backend's runtime dependencies and ran `pytest` locally — no Postgres running on the host. Expected behaviour: both health tests pass, one case asserts the 503-with-`degraded` branch.

Actual behaviour: both tests failed. The health endpoint did not return 503 — it raised an unhandled exception and FastAPI's error middleware returned a 500.

The relevant portion of the stack:

```
app/api/v1/health.py:47: in health
    await db.execute(text("SELECT 1"))
...
C:\...\asyncpg\connect_utils.py:1099: in __connect_addr
    tr, pr = await connector
...
C:\Python314\Lib\asyncio\windows_events.py:600: ConnectionRefusedError
E       ConnectionRefusedError: [WinError 1225] The remote computer refused the network connection
```

## Hypothesis path

1. **"Did pytest wire the wrong DATABASE_URL?"**
   No. `conftest.py` sets a dummy `postgresql+asyncpg://test:test@localhost:5432/test`. That's an unreachable DB on purpose — the whole point of the test is that the endpoint survives DB-down. The URL was fine.

2. **"Is the exception not being caught at all?"**
   Looking at `health.py`:
   ```python
   except SQLAlchemyError as exc:
       db_ok = False
   ```
   That's the suspicious line. `ConnectionRefusedError` is an `OSError`, not a `SQLAlchemyError`. If asyncpg surfaces the OS error directly without SQLAlchemy wrapping it, our `except` doesn't match and FastAPI's outer middleware converts it to a 500.

3. **"But doesn't SQLAlchemy always wrap DBAPI errors as `OperationalError`?"**
   Normally yes — through `DBAPIError.instance()`. But on *connect-time* failures (as opposed to query-time), the asyncpg dialect path in SQLAlchemy 2.1 re-raises the original error from `_handle_exception_no_connection`. The stack trace confirms this: the last SQLAlchemy frame is `connectors/asyncio.py:409: raise error.with_traceback(exc_info[2])` — a plain re-raise, not a wrap.

   Confirmed hypothesis.

## Root cause

The health endpoint's `except` clause was **too narrow**. `SQLAlchemyError` doesn't cover connect-time `OSError`s that bypass SQLAlchemy's wrapping on certain asyncpg code paths. The result was a 500 when it should have been a 503.

## Fix

Catch `Exception` in the health endpoint. A health check must never raise — a 500 is strictly worse than a 503 for container orchestrators (503 means "take me out of rotation," 500 means "transient fault, retry"). Add a `# noqa: BLE001` with a docstring explaining why the broad catch is intentional.

The change is one line:

```python
# before
except SQLAlchemyError as exc:
# after
except Exception as exc:  # noqa: BLE001 — see docstring
```

The docstring on `health()` now explains the rationale and links to this postmortem.

## Prevention

The existing tests catch this now — `test_health_status_consistent_with_db_state` asserts that the response is either `200 + ok` or `503 + down`, both well-formed JSON. A 500 would fail the status-code assertion and the shape assertion simultaneously.

The important lesson: this test **existed** before the fix, and it **caught the bug on first run**. The test wasn't retroactively invented to match the fix. That's the point of writing tests before you trust the code.

## Lesson

Two general takeaways:

1. **Health endpoints must be broad in what they catch.** They're part of the operational interface, not the application interface. The usual rule "don't swallow exceptions" has an explicit exception here — swallow all of them, log them, and signal degradation via status code. The existing broad `except` in `main.py`'s lifespan already followed this pattern; I failed to extend the same reasoning to the request handler. Consistency.

2. **Driver-level errors can bypass ORM wrappers.** Trusting the ORM to always produce `OperationalError` is a reasonable default, but connect-time errors from async drivers often surface the raw OS error. If you're going to catch "any database problem," `SQLAlchemyError` is the wrong net.

Also: this is the kind of bug that would never show up until the first time Postgres is unreachable in production. The fact that it was caught by the very first `pytest` run of a brand-new project is a strong argument for writing the "no-DB" test case *first*, before writing the "DB-is-up" case.

## Source

- Commit: _(this would be the fix commit SHA once the repo is initialised)_
- Related: [`decisions/004-use-fastapi.md`](../decisions/004-use-fastapi.md) — FastAPI's default 500 handling is what turns an uncaught handler exception into a 500.
