# Principal support contradictions fail before sketch diagnostics

## Expectation

The circular-support mutation test expected a returned document with an unresolved-sketch diagnostic.

## Actual behavior

The mutation changes the principal-plane identity while retaining the original axis and saved frame.
The owned principal-reference guard detects that contradiction during native model decoding.
The public SDK raises `ArchiveError` before the circular-sketch diagnostic path runs.
Both full and design-only reads enforce this guard.

The [failed queue job](https://github.com/TryUniCAD/Kit/actions/runs/45286601923/job/138084669209) records the failure on candidate `651d82878b20bdca9c4570b0fe4488c3c7a50b70`.

## Workaround

Integration tests for contradictory owned principal references must require the format error.
Keep unresolved-sketch assertions for the separate diameter, flags, and footer contradictions.
The [placement change](../../../../Changes/Solidworks/Inspection/Parts/SolidworksPlanePlacement.md) defines the bounded reference checks and their remaining qualification limits.
