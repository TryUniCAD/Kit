# A coplanar oblique rim can move off its cap during unit conversion

A small displacement of an oblique bore centre can be exactly transverse
in binary64 millimetres. After division by 1000, the independently rounded
coordinates can have a nonzero axial displacement in metres. Rounding
the native coordinates back into millimetres can also hide small
differences. Both effects are visible with exact dot products of the
represented values.

Use the actual cap origin and signed analytic axis. Prove the two circle
centres lie on their owned planes and their difference is parallel to
the same wall in each unit system. Validate raw typed coordinates before
normalizing the geometry for the SDK. A conversion that cannot prove its
cap placement must refuse the shape instead of moving the centre.
[Exact model and wire contrasts](../../../../../re/solidworks/records/ObliqueLocalBores2026.md)
