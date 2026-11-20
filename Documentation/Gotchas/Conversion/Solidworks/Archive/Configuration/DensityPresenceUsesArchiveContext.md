# Density presence uses archive context

A current `moDensityParameter_c` has its own lightweight base and stored
`f58` double. Its `f68` byte is present outside archive condition
`0x80`. A nonzero byte introduces a further double and native runtime
normalization.

Qualify the archive mode before reading those fields. The ordinary
lightweight suffix accepts the presence byte zero and retains the original
`f58`. Material identity and appearance use separate native owners.

[Exact native branches and observed part frames](../../../../../../re/solidworks/records/ConfigMaterialSlice2026.md)
