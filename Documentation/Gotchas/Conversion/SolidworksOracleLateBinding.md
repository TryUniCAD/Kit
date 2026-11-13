# SOLIDWORKS oracle late binding

## Expectation

PowerShell or .NET dynamic COM should open a healthy SOLIDWORKS instance and return geometry.
The same live instance should reliably serve `Marshal.GetActiveObject`.

## Actual behavior

The oracle installation can raise `TYPE_E_ELEMENTNOTFOUND` during type-library scanning.
`Marshal.GetActiveObject` can also fail with `MK_E_UNAVAILABLE` while VBScript `CreateObject` succeeds.
Windows scripting `VBArray` conversion and direct indexing do not cover every return shape from this API: the single-body result may be direct dispatch, and numeric arrays need native-idl conversion.

## Workaround

Use raw `IDispatch::GetIDsOfNames` and `IDispatch::Invoke` for measured geometry, which avoids type-library discovery and gives normal .NET arrays for volume and centre of mass.
Use `Activator.CreateInstance` with the registered ProgID when connecting through .NET.
Use VBScript for direct late-bound feature edits: a depth assignment to `Dimension.SystemValue`, a rebuild, and closure without saving worked reliably for parameter acceptance.
Do not use arbitrary `cmd.exe` hops when invoking an oracle reader; read the active document or persist a report file directly.
See [the working oracle harness](../../re/tooling/harness/OracleMeasure.cs) and [the measured five-line case](../Changes/SolidworksFiveLineNativeHistories.md).
