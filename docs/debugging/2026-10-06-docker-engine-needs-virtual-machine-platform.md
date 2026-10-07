# 2026-10-06 — Docker Desktop is installed but the Linux engine cannot start

**Severity:** high (blocks local compose verification)
**Time to find:** ~20 minutes of `docker version` hanging / returning HTTP 500
**Area:** infra

## Symptom

`docker version` prints a working **Client** (29.8.2) then fails:

```
request returned 500 Internal Server Error for API route and version
http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/v1.56/version
```

`Docker Desktop.exe` and `com.docker.backend` are running. `docker compose up` cannot start because there is no engine.

## Hypothesis path

1. **Docker isn't installed.** Ruled out: client version prints, `C:\Program Files\Docker\Docker\Docker Desktop.exe` exists.
2. **The daemon is still booting.** Ruled out: backend log showed the engine go `starting → stopping → stopped` within ~20 ms of launch, then stayed stopped for over an hour.
3. **WSL is installed but the distro is stopped.** Ruled out: `wsl --status` / `wsl -l -v` print the *inbox stub* usage text for `wsl --install`. That is the Windows `wsl.exe` that exists before the WSL optional component is enabled — not a real WSL install.
4. **Hyper-V backend as a fallback.** Ruled out from Docker's own GUI settings payload: `vm.hypervisor.windows.hyper-v.disabledReason` = `"Windows Home can't run the Hyper-V backend"`.

## Root cause

`com.docker.backend.exe.log`:

```
attempting recovery from engine failure: starting engine: engine linux/wsl failed to start:
checking preconditions: Virtual Machine Platform not enabled
```

Docker Desktop on this machine uses the **linux/wsl** engine. That engine requires the Windows optional feature **Virtual Machine Platform**. It is not enabled. Windows Home cannot use Hyper-V instead. Enabling the feature requires elevation (and typically a reboot). An unprivileged attempt to `dism /enable-feature` was declined.

## Fix

Not applied in this session — it is a host OS change, not an application change.

On the development machine:

1. Enable **Virtual Machine Platform** and **Windows Subsystem for Linux** (Settings → Optional features, or `wsl --install --no-distribution` from an elevated prompt).
2. Reboot.
3. Confirm `wsl --status` reports a real WSL version, then `docker info` succeeds.
4. Re-run `docker compose up --build` from `mallmind/`.

Until that happens, Phase 0b Docker rows in the README verification matrix stay unverified. They must not be marked ✅.

## Prevention

The verification matrix already distinguishes "written" from "verified." This bug is why: installing Docker Desktop is not the same as having a running Linux engine.

## Lesson

On Windows, "Docker is installed" is three separate facts: CLI on PATH, Desktop UI process, Linux engine actually running. The CLI 500 against `dockerDesktopLinuxEngine` is a *symptom* of a failed engine start. The backend log's precondition check (`Virtual Machine Platform not enabled`) is the cause. Always read the engine log before retrying `docker info` in a loop.
