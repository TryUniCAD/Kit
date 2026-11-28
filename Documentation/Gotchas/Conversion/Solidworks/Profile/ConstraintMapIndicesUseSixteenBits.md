# Constraint-map indices use sixteen bits

## Expectation

The value-array append returns the actual array index.
Its optional constraint-map registration could appear to preserve the same width.

## Observed behavior

The 2026 append passes the low 16 bits of that index to registration, widened with zeros.
The map descriptor stores that narrowed value with the value-array class namespace.
Append still returns the full index.
Lookup without the optional map scans and returns full array indices.
The two paths therefore have different index-width boundaries.

## Workaround

Track the full array index and the optional descriptor index separately.
Do not treat the descriptor as a persistent dimension ID or archive reference.
Do not infer correct optional-map behavior for indices outside the recorded 16-bit boundary.
The [arc-reference record](../../../../../re/solidworks/records/ArcDimensionReferences2026.md#append-and-optional-index-registration)
contains the exact narrowing and lookup operations.
Large-array native behavior remains unmeasured.
