<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Windows launch authorization

## Behavior

A08g holds each Windows session's initial thread inside its private Job Object while the supervisor publishes process metadata.
The supervisor then renews the current single-job or grouped leases and validates their execution deadlines.
Only a successful authorization releases the worker.

Metadata publication failure, a replaced supervisor owner, an expired lease, or an elapsed execution deadline terminates the held process.
One stale grouped member prevents the whole grouped worker from starting.
The existing setup-failure settlement remains responsible for retry decisions.
Initial-thread handles close after release, hard termination, or process cleanup.

Direct `WindowsProcess` callers retain their existing eager startup.
This includes the warm claim helper and the application watchdog.
Their existing process and ownership checks still apply.

The implementation uses the existing native suspended-thread and Job Object APIs.
Microsoft documents the suspend count returned by `ResumeThread` and termination when the final Job Object handle closes. [ResumeThread](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-resumethread), [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)

## Verification

The nine new Windows process cases passed locally on Python 3.14.6 with the locked development extra.
They cover successful single and grouped settlement, metadata failure, owner replacement, expired leases, elapsed deadlines, a stale grouped member, owner death, and eager-call compatibility.
Refusal cases prove that the worker entry marker is absent and its native Job Object is empty.
Successful sessions observe published metadata and terminate their retained descendants.

```shell
rtk test python -m pytest -q -p no:cacheprovider --import-mode=importlib tests/Research/Windows/Launch
```

This verification exercises the real controller, supervisor sessions, operating-system processes, and Job Objects.
The broader selection passed all 18 cases, including existing recovery, claim-helper, pool, input, tree, and timeout coverage.

```shell
rtk test python -m pytest -q -p no:cacheprovider --import-mode=importlib tests/Research/Windows/Launch tests/Research/Windows/WindowsRecoveryTests.py tests/Research/Windows/WindowsClaimTests.py tests/Research/Windows/WindowsPoolClaimTests.py tests/Research/Windows/WindowsInputTests.py tests/Research/Windows/WindowsTreeTests.py tests/Research/Windows/WindowsTimeoutTests.py
```

The interpreter came from the shared environment synchronized with `uv sync --frozen --no-default-groups --extra dev --python 3.14`.
Remote regression and merge-group acceptance require their own revision-bound results.
The two-week operating pilot retains its separate elapsed-time requirement.

See the [startup gotcha](../../../Gotchas/Research/Supervisor/WindowsStartupAuthorization.md) and [supervisor reference](../../../Reference/Research/ResearchSupervisor.md).
