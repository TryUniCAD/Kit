# Saved radial text can leave the sketch plane

A Front-plane radius dimension can store a text point with a nonzero
component normal to the sketch. On the original and edited D01 source
part, the actual radial display owns `f6a0.f38.z=0.0001` metres.
The independent sketch plane and the circle both remain at zero Z.

Preserve or explicitly refuse this owner in source projection. The
ordinary circular constructor currently derives text from a two-dimensional
local point and emits a label in the sketch plane. The source observation
does not establish how a new radial normal offset should be authored.
[Disclosed comparison](../../../../../re/solidworks/records/ConcentricD01DesignBridge2026.md)
