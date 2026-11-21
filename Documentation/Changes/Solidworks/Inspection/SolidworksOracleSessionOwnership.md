# Preserve existing SOLIDWORKS oracle sessions

The shared `Swapp.py` oracle controller now refuses existing SOLIDWORKS application processes before COM activation.
It verifies the returned process ID before changing application properties.
Cleanup commands require a registered fresh process.
An initialization failure with unknown ownership releases its COM reference without closing documents or exiting the application.

The legacy `sweep()` entry point now waits briefly and checks that the application is absent.
It no longer terminates processes by image name.
An existing or hung session makes the batch fail before document access.
The owner must resolve that session before another fresh batch can start.
The inspection helpers record this refusal at the `oracle_idle_guard` stage.

Dialog handling now uses registered process handles with `SYNCHRONIZE` access.
Only live owned process IDs enter its window filter.
The handler checks ownership again before sending a dialog response.
It also verifies that the selected button belongs to that process and dialog.
Responses use a two-second native message timeout.
A monitor that fails to stop records a cleanup failure.
Closing the controller waits for confirmed process exit before releasing its registration and handle.
An exit timeout records a failure and retains the registration.
Microsoft documents the [process-handle access](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openprocess)
and [nonblocking lifetime check](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject).

Curve-worker timeout cleanup also checks the recorded process creation time through a newly opened handle.
A reused PID or missing creation identity blocks termination.
The controller terminates only the matching process object and waits for its exit.
It sends no image-wide or process-tree termination command.
The [native creation-time API](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes)
provides the exact 64-bit `FILETIME` recorded by `OracleIdentity.py`.
The [timeout identity gotcha](../../../Gotchas/Conversion/Solidworks/Tracing/OracleTimeoutCleanupNeedsCreationIdentity.md)
records the earlier stale-PID cleanup boundary.

`ProbeIdleGuard.py OUTPUT --expected-pid PID` observes the idle guard through native process enumeration.
Stage the committed probe and helper in the guest-readable oracle directory.
Use a new report path and a known existing unowned process ID.
The probe records tool hashes, the refusal and before/after process sets.
It uses no COM, document, dialog or cleanup operation.
Pair its report with the exact oracle identity when recording native evidence.

Verification includes source inspection, Python syntax parsing and scoped diff checking.
The [native guard observation](../../../../re/solidworks/measurements/2026/OracleSessionGuard.json)
recorded the refusal on executable `34.5.2.0604`.
The same process creation identity and document metadata remained unchanged before and after the guard.
Its two documents included one unsaved modified drawing.
The probe's owned-process registry remained empty.

Fresh-instance registration, dialog responses, graceful exit and forced timeout cleanup still require native observations.
No local repository tests ran.
This change adds no writer capability or geometry acceptance.
