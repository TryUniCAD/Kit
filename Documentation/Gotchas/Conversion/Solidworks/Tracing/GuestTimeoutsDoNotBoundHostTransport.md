# Guest timeouts do not bound a stalled host transport

## Expectation

A 240-second guest worker timeout ensures that the macOS caller receives a timeout result and can safely start the next oracle batch.

## Observed behavior

The oracle owner observed source-preflight execution `88320` stalled during `ControlRectangle` verification.
The last persisted stage was `OpenDoc6` for more than ten minutes, despite the guest dispatcher's configured 240-second worker timeout.
No timeout result was persisted.
A separate current-user process inventory also failed to return.

A read-only VM capture showed the control UI without establishing whether its application process was making progress.
The owner's pause attempt failed, a subsequent VM reset was confirmed, and the old host source execution returned `255`.
The separate old inventory transport was terminated only after its exact command identity was checked.
The first boot-time current-user probe returned `255` because no execution session was available yet.
A later current-user `cmd /c ver` succeeded, and a completed process inventory returned `0` with no main `SLDWORKS.exe`, `python.exe`, `sldProcMon.exe` or `WerFault.exe` observed.
Normal background services were left untouched.

The source batch remains unfinished and invalid for acceptance.
Neither requested annulus nor capsule candidate was measured.
The [sanitized interrupted record](../../../../../re/solidworks/measurements/2026/CurveSourcePreflight07Interrupted.json)
retains the completed control authoring and incomplete reopening evidence with their original hashes.
The observations do not establish why the guest timeout failed to produce a result.
They do not identify a capture-pipe problem, guest-clock behavior, native format defect or application crash cause.
The reset and old-transport cleanup were owner recovery actions, not automated supervisor behavior.

## Workaround

Use the [host deadline supervisor](../../../../../re/tooling/sw2026/RunOracleBatch.py) with a new host progress/output root and a separate host report.
Its host monotonic timer is independent of the guest worker's timeout.
Its live `Popen` object identifies only the transport it launched.
Progress-file signatures supply observations, not proof of job completion.

On a deadline, stop only that owned host transport through bounded terminate/kill waits.
Keep `guest_state_unknown=true` and `acceptance=false` even when host termination succeeds.
Inventory and recover the guest before another batch; do not automatically retry, terminate guest applications or reset the VM.
An absent or stale record is not a terminal process state.

The [change entry](../../../../Changes/Solidworks/Inspection/SolidworksOracleHostDeadline.md) documents the new host command, report placement and verification limits.
Python documents [polling, waits and child-only signals](https://docs.python.org/3/library/subprocess.html#popen-objects) separately from the [host monotonic clock](https://docs.python.org/3/library/time.html#time.monotonic).
The source stall is evidence for an independent supervision boundary, not a verified explanation of the earlier missing timeout.
