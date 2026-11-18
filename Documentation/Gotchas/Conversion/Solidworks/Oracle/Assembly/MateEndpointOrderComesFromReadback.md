# Mate endpoint order comes from native readback

The D02 perpendicular source selected the second occurrence's Right Plane
first. `MateEntity(0)` returned the first occurrence and the point and
normal of its Top Plane. Selection order alone gave the observer the wrong
expected owner.

Validate every returned endpoint against its authored occurrence and datum.
Retain the actual native order when comparing saves and reopens.

[Native ordering evidence](../../../../../../re/solidworks/measurements/2026/PerpendicularMateSourcePosition04.json)
