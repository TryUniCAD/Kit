# Construct explicit ordinary planar mate groups

The internal SOLIDWORKS SDK constructor can now share one actual generated part
across a complete direct component list and build ordered coincident, parallel
and positive distance mates with explicit occurrence and child datum endpoints.
Use `MakePlanarGroup` with typed `OccurrenceIn`, `GroupMateIn` and `PlaneEndIn`
inputs and one actual fixed occurrence index. The prior pair interface retains
its existing behavior and bytes.

The admitted profile is visible, resolved, rigid and external, with initially
satisfied aligned same-axis principal planes and positive unflipped distance.
Unsupported component state, datum families, dimension forms and inconsistent
or partial graphs fail explicitly. No public writer is enabled.

Frozen process evidence covers six actual dimensioned-child groups with two,
three and five components, both endpoint orders and first/last anchors. Every
complete bundle matches the independent mathematical composer, eight invalid
inputs emit no bundle, all 30 prior flat bundles and both recursive layouts
retain exact bytes, and 1,740 typed stream round trips pass across 142 identified
successful workers. No CAD or sealed input is read by generation. New native
acceptance and the original locked-case evaluation remain separate gates.

[Constructor rules and verification](../../../../../../re/solidworks/records/SdkPlanarGroupConstruction2026.md)

[Original source-lock evaluation protocol](../../../../../../re/solidworks/records/SdkOriginalPlanarMateEvaluation2026.md)
