# A revolve angle alone does not define an editable axis selection

A valid full or partial revolve can retain an angular dimension while the older marker reader exposes only a native feature fallback. Filling an axis ID from the profile ID or using construction coordinates as a fixed constraint does not repair ownership.

The disclosed modern SOLIDWORKS 2026 path stores its live angle under the actual end/display/dimension/parameter graph, and its selected axis under a separate local component sketch-entity handle. The native line array index, permanent mark and line creation ID have different meanings. A neutral `AngularRevolve` needs the actual positive radian parameter, a linked `Selection` and a real construction entity in its source sketch.

Resolve all owners together. Keep construction geometry outside the contour and preserve only actual solver relations. Reverse sweep changes the effective axis direction rather than the source line or positive angle. Validate the composed neutral document before publishing a projected method; if its model limits reject an unsupported span, retain the earlier source representation. Full-turn geometry alone proves neither a driving parameter nor a selected line.

[Typed public reader and exact process evidence](../../../../../../re/solidworks/records/SdkOrdinaryRevolveRead2026.md).
