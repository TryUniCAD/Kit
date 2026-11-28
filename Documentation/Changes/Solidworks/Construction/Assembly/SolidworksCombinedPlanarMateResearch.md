# Construct ordered planar mate groups in research

The SOLIDWORKS 2026 research composer accepts a sequence of aligned
coincident, parallel and driving distance mates between resolved occurrences
of one generated part. Each request selects two actual principal planes.
The group shares one fixed occurrence and uses distinct nonempty mate names.

The composer allocates and publishes each mate in request order. Resolved
wrapper IDs belong to the assembly as a whole. Detached endpoint ordinals
belong to each mate. The configuration manager and both header archives
retain the final feature allocator state and individual mate creation logs.
The resolved feature group leaves mate publication to its linked MatesList.

The guarded [bundle process](../../../../../re/tooling/sw2026/PlanarCombinedBundleProcess.py)
built two- and three-mate designs twice, including different constraint and
occurrence orders. All seven tracked parent streams round-trip exactly.
The MatesList grows from the actual graph. Duplicate names and conflicting
fixed anchors fail before any bundle is returned. Runtime input-file reads
remain zero.

The [native author](../../../../../re/tooling/sw2026/AuthorCombinedPlanarMates.py)
created and reopened a disclosed two-mate source with healthy controls.
The [paired observer](../../../../../re/tooling/sw2026/InspectCombinedPlanarMates.py)
verified a generated pair through the distance edit from 71.375 mm to
88.625 mm, synchronized save and fresh reopen. Four distinct native processes
passed with healthy controls and 333 numeric comparisons. The complete parent
and child trees match the disclosed native control. The
[measurement](../../../../../re/solidworks/measurements/2026/GeneratedCombinedMateNative01.json)
records the exact source, builder and file hashes. Held-out qualification and
the public SDK writer remain open.

The [rotated three-mate measurement](../../../../../re/solidworks/measurements/2026/GeneratedRotatedMateNative01.json)
extends this comparison to a parallel, a driving distance and a coincident
mate, in that order. Both occurrences have a 30-degree rotation. The edit
predictor follows the actual distance normal and preserves the other mates.
The 91.125 mm edit and six datum links survive native save, fresh reopen and
public SDK readback.
