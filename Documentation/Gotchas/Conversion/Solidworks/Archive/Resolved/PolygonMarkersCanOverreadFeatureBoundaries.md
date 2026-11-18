# Polygon markers can overread feature boundaries

An ordinary polygon can have valid typed line and point arrays while the visible-marker scan misses its entire loop or labels its final line as a native spline.
The disclosed three-sided SDK part produced two lines plus a native curve; the six-sided part produced no sketch entities.
The inferred final span could include the following extrusion class.
Changing only the bounds would leave incorrect sketch semantics.

Use the actual `moProfileFeature_c.pd_f80 -> sgSketch` ownership and separate point/line arrays.
Resolve compact or extended endpoint indices in the point-array domain and incident handles in the line-array domain.
Keep creation IDs, permanent markers and archive-map IDs separate.
Require actual closed-ring/adjacency evidence before replacing the legacy projection, and retain unsupported curves, constraints and extra point roles.

The [typed line-loop record](../../../../../../re/solidworks/records/TypedLineLoops2026.md) and [40-process receipt](../../../../../../re/solidworks/measurements/2026/TypedLineLoopsSdk01.json) bind the repair and disclosed before/after native-save comparisons.
