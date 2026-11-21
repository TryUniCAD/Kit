# Calibration failure needs an operation

A failed calibration should identify which operation prevented measurement.
The Windows sweep at `077e7d1a` stopped in its first trial after 1.55 seconds,
with no completed jobs. A separate candidate at `e3059891` passed the sweep
and stopped during the decoder-rejection case before observing the expected
child refusal. Both reported `measurement_or_supervision_error:PermissionError`.
The artifacts retained the exception class without its operation or numeric
error codes. [Sweep failure](https://github.com/TryUniCAD/Kit/actions/runs/44838101316/job/136639783189) · [Decoder-rejection failure](https://github.com/TryUniCAD/Kit/actions/runs/44839678773/job/136645077140)

Use the `supervision_error` detail to distinguish launch, process sampling, log
handling, and stop operations. A Windows error code is included when the
exception supplies one. The two historical reports do not identify the cause
of the access failure. [Operator guide](../../../Reference/Research/OfflineCalibration.md)
