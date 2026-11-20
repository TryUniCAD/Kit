# Read strict geometry from a bare periodic SOLIDWORKS local body

The strict part reader accepts the measured version-19000 BaseBody
shape with two full circular edges and two planar caps. It binds the
physical LocalBodies group, live import feature, unique configuration
atom and retained rollback predecessor before building the solid.
The geometry reader reconstructs two neutral seam vertices from the
two vertex-free native circular edges.

Two disclosed cold parts retain their actual design body and match the
native volume, area, centroid and bounds. The host proof also covers
two same-locator planar cases, four ordinary native-marked controls
and eleven checks on unsupported geometry or archive ownership.
Guarded construction and readback made zero runtime file reads.

[Strict SDK readback](../../../../../../re/solidworks/measurements/2026/SdkBareCylinderGeometry01.json)
· [Native part lifecycles](../../../../../../re/solidworks/measurements/2026/GeneratedLocalCylinderPartNative01.json)
