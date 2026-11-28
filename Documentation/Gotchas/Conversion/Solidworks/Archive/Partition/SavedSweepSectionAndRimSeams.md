# Saved sweep section and rim seams can move independently

A Standard sweep's periodic Section sketch owns a distinct start/end
point, shared by both uses of the circle. The saved kernel uses its
own reference direction for each of the two physical circular rims.
Two independent native Section diameter edits moved the existing
sketch point by 17° while both kernel curve reference directions
stayed `-Z`. The same sketch point indexes and marks persisted.

Read the actual Section point and its signed frame for the editable
seam. The neutral Section seam stores a local angle and its diameter
parameter ID. Resolve the live point from the current circle center and
radius; `saved_point_mm` is the original native observation, not a driving
coordinate. Resolve the result rims through the native edge and reciprocal
FIN owners, then derive each torus chart's direction from the owning
analytic carrier. Using the surface reference as a sketch seam would
lose the observed edited point.

[Exact wire and native edit observations](../../../../../../re/solidworks/records/ScopedSavedSweepTopology2026.md)
