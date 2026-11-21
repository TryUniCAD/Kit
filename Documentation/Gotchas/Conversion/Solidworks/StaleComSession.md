# An unhealthy COM server invalidates a failure

## Expectation

An interface error while opening a file proves that the file is invalid.

## Observed behavior

The [2026 deletion study](../../../../re/solidworks/v2026/Deletion2026.md)
recorded interface error `0x800706B5` after earlier documents had closed.
A known control also failed and then passed after SOLIDWORKS restarted.
The server state invalidated that batch.

## Workaround

Retry in a fresh process and measure a known control.
Discard a batch if either control fails.
Count a candidate crash only when a healthy control establishes the oracle state.
