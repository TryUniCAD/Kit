# Preserve existing SOLIDWORKS oracle sessions

The shared `Swapp.py` oracle controller now refuses existing SOLIDWORKS application processes before COM activation.
It verifies the returned process ID before changing application properties.
Cleanup commands require a registered fresh process.
An initialization failure with unknown ownership releases its COM reference without closing documents or exiting the application.

The legacy `sweep()` entry point now waits briefly and checks that the application is absent.
It no longer terminates processes by image name.
An existing or hung session makes the batch fail before document access.
The owner must resolve that session before another fresh batch can start.

Dialog handling now uses registered process handles with `SYNCHRONIZE` access.
Only live owned process IDs enter its window filter.
The handler checks ownership again before sending a dialog response.
Closing the controller removes its registration and releases the handle.
Microsoft documents the [process-handle access](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openprocess)
and [nonblocking lifetime check](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject).

`ProbeIdleGuard.py OUTPUT --expected-pid PID` observes the idle guard through native process enumeration.
Stage the committed probe and helper in the guest-readable oracle directory.
Use a new report path and a known existing unowned process ID.
The probe records tool hashes, the refusal and before/after process sets.
It uses no COM, document, dialog or cleanup operation.
Pair its report with the exact oracle identity when recording native evidence.

Verification so far includes source inspection, Python syntax parsing and scoped diff checking.
The changed refusal, fresh-instance registration, dialog path and owned cleanup still require native observations.
No local repository tests ran.
This change adds no writer capability or geometry acceptance.
