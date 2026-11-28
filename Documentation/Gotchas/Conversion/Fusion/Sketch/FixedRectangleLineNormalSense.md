# Fixed-corner Fusion lines can store either XY normal sign

A saved rectangle with a fixed origin corner can have consistently
positive or negative Z in its four `Line3D.planeNormal` fields.
The saved baseline and five independent native archives kept the
same identity XY support and sketch placement, disabled matrix
Z inversion, and retained counterclockwise winding. Both stored
signs remain perpendicular to the saved line directions.

Validate one common signed normal aligned with the proved sketch
plane and keep it in typed state. Do not derive winding or flip a
feature from this field. A mixed-sign or off-axis set remains
unsupported.

[Exact held-out evidence](../../../../../re/Fusion/SavedCuboidRoundTrip/DisplayOrderContrast.md#fixed-corner-line-plane-normal)
