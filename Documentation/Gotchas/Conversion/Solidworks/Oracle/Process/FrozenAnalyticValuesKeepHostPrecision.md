# Frozen analytic predictions keep the host result

The macOS and Windows computations of the circular-segment formula
differed by one or two binary64 units in volume or centre of mass for
four rows. Recomputing the entire prediction mapping in the guest and
requiring exact floating point equality stopped preflight before any
native process was launched.

Freeze the model, predictions and tools on the host. Verify the exact
manifest hash in the guest and use its recorded predictions for
native comparisons at the established geometry tolerance.
[Disclosed scope contrast](../../../../../../re/solidworks/records/ThroughAllMultiStockScope2026.md#unrestricted-scope-contrast)
