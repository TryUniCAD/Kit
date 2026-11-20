# The direct cut scope body array can be unavailable

On the measured SOLIDWORKS 2026 SP05.2 two-stock through-all cut,
the definition reports `FeatureScope=True` and `AutoSelect=False`.
The direct body count is `-1` and the body array is absent. Those
values establish unavailable membership after ordinary definition
access. They do not identify which body the cut owns.

Keep the geometry observation independent. Query scope after
`AccessSelections` from a separate fresh read-only open, and release
the selection access afterward. The selection query can roll back
the model, so the geometry edit and the scope observation use
separate processes.
[Exact native refusal](../../../../../../re/solidworks/measurements/2026/ThroughAllMultiStockScopeRetry01.json)
· [Protocol](../../../../../../re/solidworks/records/ThroughAllMultiStockScope2026.md)
