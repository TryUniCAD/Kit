# Verify driving edits on the generated FreeCAD origin box

The exact generated SOLIDWORKS 2026 part from the disclosed FreeCAD origin
box opens with one solid and three live driving lengths. Its geometry,
origin anchor and thirteen file text properties survive the three
independent edits, a clean save and fresh reopen. Four fresh processes and
162 analytical checks pass with both controls healthy.

The width and length are restored individually. The depth persists at
14 mm after a native save and reopen. The strict history reader retains
the three drivers on both files and preserves four scoped streams
byte-for-byte. The freshly generated file has no readable Parasolid
payload in default strict mode. The native save carries the geometry
payload and passes that read.

The generated body is named `AdditiveBox`. The source label `Body` and the
source driver names are preserved as property and parameter bindings.
Direct native names and original benchmark membership remain open.

[Disclosed source, lifecycle and semantic status](../../../../../re/solidworks/records/SdkFreecadOriginBox2026.md)

[Sanitized native measurement](../../../../../re/solidworks/measurements/2026/SdkFreecadOriginBoxNative01.json)
