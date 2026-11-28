# Read both measured fixed-corner Fusion line normal senses

Strict Fusion reading now keeps the uniform signed line normal from
the fixed-corner rectangle proof. Either measured Z sign qualifies
on the exact XY support. The existing checks still verify the
support and sketch matrices, counterclockwise winding, per-line
direction, distinct fixed origin, constraints, driver bindings and
solved solid. Mixed signs and off-axis normals refuse.

Use `kit decode SOURCE.f3d` or the strict SDK reader. The typed
source state retains the actual stored sign through JSON. Existing
fixed-corner documents continue to use the read-only output contract.

The earlier negative-Z baseline and five independently saved
positive-Z archives use identical XY support and matrix orientation.
All five positive-Z inputs passed strict SDK JSON and matched native
body volumes. Ten corrupted variants refused. See the
[exact capture and comparison](../../../../re/Fusion/SavedCuboidRoundTrip/DisplayOrderContrast.md#fixed-corner-line-plane-normal)
and [line normal gotcha](../../../Gotchas/Conversion/Fusion/Sketch/FixedRectangleLineNormalSense.md).
