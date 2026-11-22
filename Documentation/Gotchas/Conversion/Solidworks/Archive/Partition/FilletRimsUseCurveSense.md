# Saved fillet rims use the native circle sense

The generic conic range calculation unwraps angles in the positive
direction. A saved fillet's negative circle sense can then turn its
measured 90 degree trim into a 270 degree arc.

For the verified single-edge rectangular-stock fillet, join the circular
curve to its actual edge and the matching cylindrical carrier. Reverse the
parameter axis for negative sense and recalculate the interval from the
original directed endpoints. Require a quarter turn for both cap arcs and
retain their edge and coedge identities.
[Observed readback](../../../../../../re/solidworks/records/SavedEdgeFilletSdk2026.md)
