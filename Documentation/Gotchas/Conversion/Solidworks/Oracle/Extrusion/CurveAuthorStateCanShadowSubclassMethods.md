# CurveAuthor state can shadow subclass methods

## Expectation

A source author subclass can add a `dimensions()` traversal and call it while reading a native extrusion definition.

## Actual behavior

`CurveAuthor.__init__` already assigns an instance list named `dimensions`. That list shadows a subclass class method with the same name. Calling the subclass traversal raises `TypeError("'list' object is not callable")`.

The through-all D01 observer reported its stage as `GetDraftWhileExtruding`, but both draft queries had already returned false successfully. The recorder retained the last completed native call while the subsequent Python list-call expression failed. The stage alone did not identify a failing native API.

## Workaround

Preserve the base state and name the actual feature-owned traversal `owned_dimensions()`. Check inherited initializer assignments against subclass method names before launching CAD. Compare the raw API result and the first failure together. Keep a failed observer run separate from native feature acceptance and retain healthy controls.

The [retry record](../../../../../../re/solidworks/records/ThroughAllSourceObserverRetry2026.md) and [failure receipt](../../../../../../re/solidworks/measurements/2026/ThroughAllSourceObserverFailure02.json) bind the exact source hashes and successful native queries. The seven-process retry proof includes restoring the collision under a newly valid checksum, which still fails the source-only namespace guard.
