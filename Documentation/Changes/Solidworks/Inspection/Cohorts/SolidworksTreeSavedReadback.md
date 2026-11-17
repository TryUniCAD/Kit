# Read generated parts after native saves and edits

SOLIDWORKS saved six derivatives of the two generated parts in the
[paired measurements](../../../../../re/solidworks/measurements/2026/TreeParityInspection01.json).
Kit now has a research readback check for each original save, radius/depth edit
save and edited fresh reopen. It compares the complete primary and linked
archives, then checks the actual sketch, driving values, fixed-centre relation,
extrusion direction, markup folder and persisted view.

The [fixture manifest](../../../../../re/solidworks/v2026/corpus/tree-parity-saves/Manifest.json)
ties each prepared file to its original save hash and the independently
recorded geometry and pose. The controlled preparation processed only the six
candidate derivatives and 240 streams. It recorded 120 same-length metadata
redactions and retained six visually reviewed previews. It did not execute
archive schemas or reparse prepared containers. Original native references
were not used for preparation.

The new process check runs in the remote native format compatibility job.
Prepared derivatives are reader fixtures; they do not add generated outputs,
qualify another feature family, or change the read-only public adapter.

The [first remote attempt](../../../../../re/solidworks/measurements/2026/TreeSavedReadbackAttempt856a.json)
passed three Front-plane derivatives and failed the other three at the first
direction-sensitive sketch matrix coefficient. The corrected check verifies
the independently recorded model-to-sketch transform, including its inverse
relationship to the observed world-space frame. The fixture bytes are identical.
The [native field record](../../../../../re/solidworks/records/ProfileTransformDirection2026.md)
also identifies the opposite-direction seed in the unchanged frozen writer.

The [corrected remote check](../../../../../re/solidworks/measurements/2026/TreeSavedReadbackProcessesEfe1.json)
passes all 54 archive comparisons, 108 semantic values and 102 pose values.
Every graph has zero unresolved references and one typed markup folder. All
102 pose values and 102 of 108 semantic values are exactly equal; the remaining
six semantic comparisons match to six significant figures. The native format
job passes 205 cases and skips 158; the policy phase passes 171.
