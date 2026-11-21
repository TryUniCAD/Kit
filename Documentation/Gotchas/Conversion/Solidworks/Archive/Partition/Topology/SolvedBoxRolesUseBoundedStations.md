# A native solved box can have two upper station values

The two exact saved F14a models carry upper Y at both `29.999999999999993` and `30.0` mm after the earlier native Width edit and restoration. Their corresponding planar and linear carriers retain the small tilt, with off-axis component `3.469446951953614e-16`. Exact station deduplication invents a third Y role even though all eight corner owners remain distinct and the physical edge/face graph is closed. [Exact saved wire receipt](../../../../../../../re/solidworks/measurements/2026/SdkFreecadF14aTopologyLineage01.json)

For this narrow geometry comparison, classify coordinates against the actual driver dimensions with the declared binary64 bound, then verify each original point against the actual carrier equation and incidence. Keep all measured coordinates and normals intact. [Scoped comparator](../../../../../../../re/tooling/sw2026/f14a_lineage/BoxTopology.py)
