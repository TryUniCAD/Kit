# Saved snapshots can retain an earlier sketch sheet

## Expectation

A rectangular extrusion snapshot contains one solid and two planar profile sheets. Every sheet uses the current driving dimensions.

## Actual behavior

The additional controlled saves contain four body roots and 202 records. The ASM header counts five roots because it also counts the ASM header record. The passive-ID scan maps the first three bodies to the current extrusion tool, selected region, and sketch. The last body retains an older passive identity and the earlier rectangular footprint. It has no current topology-cache consumer.

Dimension annotation extension coordinates can also retain the previous dimension location after a size decreases. The measured endpoints and distance update correctly.

## Workaround

Keep the current solid, current sheets, and retired sheet separate. Validate passive identities, complete disjoint record ownership, source curve tags, and sheet topology. Preserve the retired sheet in typed native state. Do not count it as a physical design body or regenerate it from current dimensions.

Preserve finite annotation extension coordinates on their declared axis. Continue to verify current measured endpoints, values, annotation plane, and parameter bindings.

See [the controlled observations](../../../../../re/Fusion/Reconstruction/NativeEditedPrisms/Findings.md) and [the reader change](../../../../Changes/Fusion/FusionSavedPrismEdits.md).
