# An open shell stores an auxiliary edge beside the removal list

Scanning for familiar reference markers in a saved SOLIDWORKS 2026 shell can
suggest two selected faces. The disclosed `moShell_c.f828` actually stores
one `moCompFace_c`. Its EndFace role 1 resolves to the top cap of the earlier
stock extrusion. The separate `f848` member is a `moCompEdge_c` with its own
edge and incident-surface carriers. Treating a surface role from that edge
as a second removal changes the design intent.

Read the explicit `f828` list and verify its local component, body atom,
stock creation event and typed face carriers. Read the auxiliary edge as
a separate ownership check. The
[paired archive observations](../../../../../re/solidworks/records/SavedOpenShellReader2026.md)
also show why displayed thickness copies cannot replace the live
`ThreeDRadiusDim_c` parameter.
