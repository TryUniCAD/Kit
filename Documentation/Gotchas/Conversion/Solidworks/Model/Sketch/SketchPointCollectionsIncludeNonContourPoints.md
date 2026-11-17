# Sketch point collections include non-contour points

An origin-anchored rectangle can have four ordinary vertices and a fifth point in its persisted sketch point collection. The additional point represents an external reference. The contour still has four edges. A guard that compares the total point count with the edge count rejects the sketch if the external point has already been attached.

Build and bind the analytic body from the ordered four-edge contour. Attach and validate the separate reference point and its relation before serializing the sketch, and preserve the contour's ownership. The guarded comparison retains the rejected first attempt and the corrected construction. [Guarded receipt](../../../../../../re/solidworks/measurements/2026/GeneratedRectangleAnchorGuard01.json)
