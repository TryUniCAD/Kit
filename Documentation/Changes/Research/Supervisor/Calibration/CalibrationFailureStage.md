# Report the first calibration supervision failure

An offline calibration that stops on an exception now records the supervision
stage, exception type, and available POSIX and Windows error codes in
`Trial.json` and `Calibration.json`. The exception's message and filename stay
out of that diagnostic. The first detail also survives a later cleanup error
in the CLI's failure report. [Operator guide](../../../../Reference/Research/OfflineCalibration.md)

Hosted calibration assertions show the detail for an unexpected exit or an
unexpected Windows decoder-rejection stop reason. A Windows process case
injects an access denial during worker memory sampling and checks the saved
detail, incomplete sweep, and empty owned state. The Windows case runs in the
existing merge queue platform job. [Calibration gotcha](../../../../Gotchas/Research/Supervisor/CalibrationFailureNeedsStage.md)
