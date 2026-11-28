# Check whether versioned COM activation creates a separate process

`re/tooling/sw2026/ProbeInstance.py` records the SOLIDWORKS process IDs before
activating `SldWorks.Application.34`, then checks the returned application's
actual process ID and executable identity before changing any application
property or calling any document API.

If activation returns a preexisting process, the probe releases its reference
and reports that a separate instance was unavailable. It sends no exit command
to that process. A fresh process must match executable `34.5.2.0604`, the pinned
SHA-256 and x64 architecture. The probe exits only that newly returned process,
waits for confirmed exit, and records which preexisting process IDs remain.
Creation of another COM object is not assumed to create another process.

Stage the committed probe, `Swapp.py`, `AuthorCurves.py` and `OracleIdentity.py`
in a guest-readable research directory, then run it through current-user
Parallels execution with a new report path. This is an owner-controlled oracle
diagnostic, not a writer or a geometry test. It opens and creates no documents,
does not sweep processes, and does not establish native feature acceptance.
If activation or identity capture hangs, the partial report is evidence of the
last completed stage; unknown process ownership does not authorize cleanup.

Verification includes Python syntax parsing, scoped diff checking, and a
controlled native probe on the pinned executable. Activation returned a
preexisting process, so the probe released its reference without an exit command.
The later read-only inspection found an unsaved modified drawing in that hidden,
user-controlled session. No local repository tests ran. The
[native evidence](../../../../re/solidworks/measurements/2026/OracleInstanceReuse.json)
and [session-reuse gotcha](../../../Gotchas/Conversion/Solidworks/Tracing/VersionedComActivationCanReuseUserSession.md)
record the distinction between COM activation and process ownership.

`OracleIdentity.py --existing-pid PID` can inspect a specifically selected
already-running process through versioned activation when it is absent from
the active-object table. It requires that PID to exist beforehand and rejects
a returned PID mismatch before reading document metadata. It records document
count, title/path/save flags, visibility and user-control state. It changes no
application property and opens, saves and closes no document or application.
