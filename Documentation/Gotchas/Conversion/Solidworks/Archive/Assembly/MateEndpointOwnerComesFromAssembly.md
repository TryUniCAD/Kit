# Mate endpoint ownership comes from the assembly list

The ordinary Config-0 readback contains occurrences in the owning assembly's
feature list. A decoded occurrence can lack the constructor's in-memory
`owner` binding. The separate mate chain still carries the actual assembly
object in its archive tag.

Pass the containing assembly into endpoint generation and verify occurrence
membership by identity. Reuse the occurrence's existing external-feature
entry and backlink. [Construction and readback evidence](../../../../../../re/solidworks/records/AssemblyPlanarEndpointConstruction2026.md)
