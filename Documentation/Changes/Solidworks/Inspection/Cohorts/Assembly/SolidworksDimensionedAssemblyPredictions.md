# Freeze dimensioned assembly predictions before native comparison

The prediction tool composes ordinary placed assemblies from the locked
authored placement specification and the independently authored L1 child.
Each trial records its own generated pair, neutral writer request and archive
checks. The reference binder verifies those hashes before reading the
independently authored, locked native results.

Use `PrepareDimensionedAssemblyPredictions.py --help` and
`BindDimensionedAssemblySources.py --help` with the
[held-out protocol](../../../../../../re/solidworks/records/DimensionedAssemblyHeldoutProtocol2026.md).
The generated discovery rehearsal reproduced the original six parent and child
hash pairs and all six neutral request hashes from 3,462 pinned source files.
It used only the two disclosed placement designs. The protocol covers a
single shared rectangular child with floating rigid placements and no mates.
