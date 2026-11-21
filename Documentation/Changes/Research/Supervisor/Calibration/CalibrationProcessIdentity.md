# Verify the recorded calibration process has exited

The Windows calibration integration checks each launcher and interpreter
against the PID and creation time recorded during the run. It uses the same
kernel creation-time observation as calibration and keeps the 15-second
cleanup deadline. A live matching process or an unavailable identity
query still fails the check.

A Windows process case exercises the same PID with a different creation
time, verifies the actual live process still fails its exit check, and
releases it before checking the recorded identity again. The fixture retains
its ten-second exit deadline and reports a timeout after explicitly cleaning
up the launched child under a bounded wait. The case uses the existing
platform queue. [Process witness](../../../../../tests/Research/Windows/Calibration/CalIdentityTests.py) ·
[Bounded fixture teardown](../../../../Gotchas/Research/Supervisor/PopenContextWait.md) ·
[Original queue failure](../../../../Gotchas/Research/Supervisor/CalibrationPidIdentity.md)
