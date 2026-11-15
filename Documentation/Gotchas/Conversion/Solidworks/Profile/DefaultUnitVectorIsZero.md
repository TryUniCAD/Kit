# The native default unit vector is zero

## Expectation

The default `mgUnitVector_c` constructor creates a canonical nonzero axis

## Actual behavior

In the locked SOLIDWORKS 2026 `sldmgu.dll`, constructor `0x31f19380` passes three zero doubles to the vector constructor at `0x31dd3a00`
It does not choose X, Y or Z
Display constructors contain both default unit-vector construction and explicit calls to `xAxis()` or `yAxis()`
Treating both operations as an X-axis default changes the resulting graph

## Workaround

Model each native operation separately
Use a zero vector for the inspected default constructor and an axis only where the caller explicitly requests one
Do not infer a nonzero vector from the class name

See [the constructor ledger](../../../../../re/solidworks/records/ProfileConstruction2026.md) for the display call sites and binary binding
