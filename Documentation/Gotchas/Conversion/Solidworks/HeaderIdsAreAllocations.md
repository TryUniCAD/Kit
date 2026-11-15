# Header identifiers record allocation history

## Expectation

The header id value is always `24 + 2 × feature_count`.

## Observed behavior

The 2026 `moHeader_c.getHighestID` method returns `f08 - 1`.
`getNewID` increments the next-id member and skips reserved identifiers.
The ladder formula describes one allocation history. It is not a format rule.
The [header field study](../../../../re/solidworks/records/HeaderConstruction2026.md)
records the binary addresses and remaining unknowns.

## Workaround

Allocate persistent identifiers from the complete emitted graph.
Derive the saved next-id state from those allocations.
Do not derive it from the number of visible features alone.
