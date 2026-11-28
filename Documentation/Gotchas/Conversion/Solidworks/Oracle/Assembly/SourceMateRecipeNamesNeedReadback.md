# Source mate recipe names need readback

The original `AuthorAssemblySources.py` and `AssemblyMateEvidence.py` helper
do not assign the optional recipe mate name to the new feature. The helper
selects the requested principal planes and calls `AddMate5`, then retains
SOLIDWORKS' assigned feature name. A `name` value in the input does not prove
that the source file contains it. This is behavior of that author harness,
not a restriction on renaming mates through the native API.

The source lock pins `AuthorAssemblySources.py` at
`6caeac4479b9a637424727c66631adc0a4ea180f87b821218924c3f8b6c0bea4`
and `AssemblyMateEvidence.py` at
`5c04a6032d5e874bcd15fc2f12fc46b138328436a1280f1deae250444a6a85a1`.
Its `author_plane_mates` path contains no corresponding feature-name setter.
The disclosed A22 source and a generated N3 group qualify the executable
semantic projection without opening the original held-out files.

Read the actual ordered mate names through the complete typed SDK graph, verify
their kinds and occurrence/datum endpoints against the independent recipe,
and forward only the authored names into the new neutral request. Do not fit a
native name counter or copy native IDs, cache values or recorded data. Preserve
the exact source/generated native tree comparison after generation.

[Frozen method, evidence and privacy boundary](../../../../../../re/solidworks/records/SdkOriginalPlanarMethodFreeze2026.md)
