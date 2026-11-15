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

Verification at publication is Python syntax parsing and scoped diff checking.
The exact installation's multi-instance behavior remains unverified until the
owner's controlled probe. No local repository tests ran.
