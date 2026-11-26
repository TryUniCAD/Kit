# Fusion oracle startup on Windows

## Expectation

A version-specific Fusion launcher can appear to be the correct entry point for a fresh native measurement process.

## Actual behavior

During measurements on Fusion 2706.1.17, direct use of the version-specific launcher opened an **Error Launching Streamed Application** dialog.
The installed Autodesk Fusion desktop shortcut reached the licensed Home tab and the local oracle bridge.

The first task-owned process also hung during graceful exit after it closed the measured documents.
The control receipts confirmed zero open documents.
A guarded restart of the recorded task-owned process restored fresh-process measurements.

## Workaround

Start Fusion with its installed desktop shortcut.
Verify that the expected build is active and the task-owned process has zero open documents before starting a measurement.
Request graceful exit and verify that the recorded PID exited before starting the next stage.
If exit hangs, inspect the task-owned PID and its completed receipts before taking any recovery action.
Preserve unrelated Fusion sessions.

See the [Fusion cuboid oracle procedure](../../../../../re/Fusion/LocalOracle/EncoderRoundTrip/README.md).
