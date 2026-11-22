# Saved radial text can leave the sketch plane

A Front-plane radius dimension can store a text point with a nonzero
component normal to the sketch. On the original and edited D01 source
part, the actual radial display owns `f6a0.f38.z=0.0001` metres.
The independent sketch plane and the circle both remain at zero Z.

Preserve or explicitly refuse this owner in source projection. The
default circular constructor still derives text in the sketch plane.
The internal owned-label input can supply the signed normal coordinate
without changing the planar leader. [Disclosed comparison and input contract](../../../../../re/solidworks/records/SdkSpatialRadialLabels2026.md)
