# Calibration cleanup needs a process creation time

Windows can assign an exited process's numeric PID to another process. A
cleanup check can therefore see a live PID after the recorded interpreter
has left its Job Object.

On merge-group revision `947ee9cb7619a846904d90fca7b9b9b49e0b6b8e`, the sweep
completed and the required Job Object cleanup assertions passed. The
separate interpreter check still saw PID 4372 after 15 seconds. The job's
artifact lacks the live process creation time, so PID reuse is an inference
for this failure. [Windows queue job](https://github.com/TryUniCAD/Kit/actions/runs/44847790065/job/136672019639)

Use the PID and exact kernel creation time from `SupervisorProcess.json`
or `SupervisorInterpreter.json` to verify each calibration process. A query
error leaves cleanup unverified. [Calibration exit check](../../../../tests/Research/Windows/Calibration/WaitForCalExit.py)
