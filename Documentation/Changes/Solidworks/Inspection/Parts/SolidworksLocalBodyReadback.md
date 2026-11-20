# SOLIDWORKS local imported body readback

A strict `convert.open_document` read with `include_brep=True` can recover a
single closed planar solid from the SOLIDWORKS 2026 SP05.2 local body stream.
Read the result from `document.brep`. The decoder selects this path for the
sole configuration zero when the ordinary decoder finds no geometry
candidates and the active partition is empty.

The local body must have a complete current-schema topology of straight
edges and planar faces with one loop per face. The selected partition and its
history must agree. Use `include_brep=False` for metadata inspection.

The two disclosed native inputs passed cold open, rebuild, save, and fresh
reopen measurements on build `34.5.2.0604`. The public integration checks
signed volume, area, centroid, topology, payload retention, and behavior
with missing history or geometry disabled.
[Fixture and measurement record](../../../../../re/solidworks/records/SdkImportedLocalBodyReadback2026.md)
