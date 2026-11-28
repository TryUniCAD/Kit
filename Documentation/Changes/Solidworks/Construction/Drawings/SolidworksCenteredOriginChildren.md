# SOLIDWORKS centered origin-linked drawing children

The private SDK origin-drawing process now constructs both corner and centered two-driver rectangle children. New `RectangleCenters.MakeCenterMut` creates the actual local center, two construction diagonals and three native coincidence owners around the existing contour and actual model origin. It reuses existing point/reference/dimension constructors and leaves the origin-display SDK source and prior caller outputs unchanged.

The child must be an ordinary version19000 canonical Front Plane rectangle, symmetric about its real same-part origin, with two complete driving distances and four axis constraints. Off-origin, incomplete and already anchored inputs are rejected. No original CAD save, vendor code or runtime research import is used by SDK construction.

Root's frozen 5,037-source replay passes 28 real processes, including four complete mathematical child counterparts, 40 exact child-stream comparisons, repeated deterministic builds and 12 explicit rejections. Both earlier corner pair containers are unchanged. Native SDK and held-out origin-drawing qualification remain pending; full public drawing writing remains gated.

[Field rules](../../../../../re/solidworks/records/SdkCenteredRectangleConstruction2026.md) · [Exact process receipt](../../../../../re/solidworks/measurements/2026/SdkOriginCenteredConstruction01.json) · [Contour/frontier ownership](../../../../Gotchas/Conversion/Solidworks/Drawings/Qualification/CenteredContoursKeepTheirOwnFrontier.md)
