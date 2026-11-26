# Windows calibration permission failure

The rejection process control expects `child_did_not_complete` and independently verifies empty claims, sessions, and job membership.
On [candidate e3059891](https://github.com/TryUniCAD/Kit/actions/runs/44839678773/job/136645077140),
153 platform cases passed and the rejection control instead reported `measurement_or_supervision_error:PermissionError`.
The same control passed on the preceding combined candidate.
The failed log contains no traceback or native error code and does not establish the failing operation.

Retry complete candidate acceptance with the existing assertions intact after reviewing this evidence.
Do not reinterpret the measurement failure as an accepted decoder refusal.
A repeated failure requires additional bounded diagnostic evidence before selecting a code repair.
