# The direct cut scope body array can be unavailable

On the measured SOLIDWORKS 2026 SP05.2 two-stock through-all cut,
the definition reports `FeatureScope=True` and `AutoSelect=False`.
The direct body count is `-1` and the body array is absent. Those
values establish unavailable membership after ordinary definition
access. They do not identify which body the cut owns.

Keep the geometry observation independent. In a separate fresh open,
measure the initial geometry or apply the upstream dimension edit and
rebuild. Then query scope between `AccessSelections` and
`ReleaseSelectionAccess`. Selection access can roll back the model.
Close without saving and verify that the original file hash is intact.
Both selection-access queries returned the same one-body owner in the
measured fixture.
[Direct getter receipt](../../../../../../re/solidworks/measurements/2026/ThroughAllMultiStockScopeRetry01.json)
· [Selection-access result](../../../../../../re/solidworks/measurements/2026/ThroughAllMultiStockScopeObserved01.json)
