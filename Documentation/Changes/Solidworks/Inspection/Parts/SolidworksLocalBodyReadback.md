# SOLIDWORKS local imported body readback

A strict `convert.open_document` read with `include_brep=True` can recover a
single closed planar solid from the SOLIDWORKS 2026 SP05.2 local body stream.
Read the result from `document.brep` and the matching summary from the
design body. This path inspects a source-backed native `Imported` feature
whose resolved base-body record matches the local storage group. The
decoder selects it when the ordinary decoder finds no geometry candidates,
configuration zero is the sole configuration, and the active partition
is empty.

Canonical plane nodes retain their native XML type for scaffold admission,
including resolved rows whose separate class marker is absent. The scaffold
check keeps the same local body and rollback validation on saved files.
[Plane type projection](../../../../Gotchas/Conversion/Solidworks/Archive/Partition/LocalScaffoldUsesNativePlaneType.md)

The local body must have a complete current-schema topology of straight
edges and planar faces with one loop per face. The selected partition and its
history must agree. A strict B-rep read raises a format error when the
required current-profile local solid fails these checks. An explicit
`strict=False` read retains the source payloads and reports
`sldprt.local_geometry_rejected`. Use `include_brep=False` for metadata
inspection.

`extract_brep` extracts native payloads with valid framing when
the geometry snapshot lacks rollback history. Document reads still
validate the snapshot before returning its solid.
[Strict extraction options](../../../../Gotchas/Conversion/Fusion/Api/StrictFusionReadValuesAreFormatSpecific.md)

The two disclosed native inputs passed cold open, rebuild, save, and fresh
reopen measurements on build `34.5.2.0604`. The public integration checks
ownership, body counts, signed volume, area, centroid, and payload
retention. Controls cover absent history, a retained history with the wrong
mark, a different group owner, and geometry disabled. The invalid
geometry controls check strict refusal and the matching partial-read warning.

The retained timeline describes the native import and its stored solid.
Editable conversion acceptance follows the
[CAD success criteria](../../../../Reference/Operations/CadSuccessCriteria.md).
[Fixture and measurement record](../../../../../re/solidworks/records/SdkImportedLocalBodyReadback2026.md)
