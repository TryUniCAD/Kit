# Typed ordinary line-loop reading in SOLIDWORKS 2026

Task `B04-SW2026-PUBLIC-LINE-LOOPS`, owner `/root/configuration_header`, delivery PR #121.
This slice repairs public reading; it changes no writer, registration, feature construction or native input.
Its exit condition is exact ordinary unconstrained polygon geometry through the public reader, including native-saved counterparts, with unsupported sketches retaining their prior representation.
Dependencies are the linked version-19000 Config/Resolved codecs, the existing ordinary profile constructor evidence and the independent neutral polygon factory.

## Cause and typed ownership

The disclosed native-qualified Skew and Step SDK parts contained valid `sgSketch` point and line arrays.
The legacy visible-marker scanner exposed two lines plus a native spline for Skew and no entities for Step, with neither closed loop.
Skew's inferred marker span extended into the following extrusion record.
A style marker or a following class token is not the primitive's owner.
The existing [rectangle collision record](RectangleSketchOwners2026.md) already establishes the same ownership distinction for circles.

The replacement reads the actual concrete schema-one `moProfileFeature_c.pd_f80 -> sgSketch` link.
The [SDK polygon ledger](SdkPolygonConstruction2026.md#geometry-ownership-and-namespaces) and [polygon construction ledger](PolygonConstruction2026.md) bind the rules to the pinned SP05.2 `sldmodu.dll`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000`.
No new binary extraction or native execution occurred in this reader slice.

| Owner or field | Read rule | Native authority |
| --- | --- | --- |
| `sgSketch.points/lines` | Their separate arrays determine primitive membership and zero-based reference domains | `0x4c5916f0` |
| Point `pos` | Actual finite local XY metres become SDK millimetres | Setter `0x4c601d10`, serializer `0x4c58f910` |
| Segment `fc8_s/fcc_s` | A compact endpoint is an actual point-array index; marker `0xffff` selects the corresponding signed extension | `0x4c590920`, endpoint lookup `0x4c5fba60` |
| Handle `idx/f18` | Marker `0x777f` selects `f18`; other values are the compact line-array index | `0x4c587800`, line lookup `0x4c5dc250` |
| Point/line `f0c` | Separate creation identity namespaces, retained as source metadata | `0x4c3e2450`, `0x4c3e3030` |
| Line `f08` | Permanent line marker, used within its actual sketch's public line identity | `0x4c4bb590`, `0x4c0cd540` |
| Point `fe8/h1/h2` | Degree two and two distinct tagged handles must agree exactly with the incident endpoint graph | `0x4c5f7e40`, `0x4c5f8460`, `0x4c602c10` |
| Point and line rows | Embedded records have no separate archive object tags or invented byte spans | Current shared `SketchFields` grammar |

The reader emits `sldprt:sketch:<profile-id>:line:<permanent-marker>`.
The entity keeps its actual creation marker, point-array endpoints, point creation identities, common entity state and display state as attributes.
Point rows remain owned vertices rather than duplicate public point primitives.
Tagged adjacency handles retain actual map indices and raw compact/extended fields in metadata.
The provenance span belongs to the real `sgSketch` owner; `embedded_array` and `row_index` identify the row without claiming a scalar-field span.

## Admission and retained limitations

Admission requires ordinary unshared profile state, the 19000 linked context, one connected ring of at least three points and lines, unique positive creation/permanent markers, finite distinct endpoints, and exact degree/incident-handle agreement.
The ring walk derives closure from actual references, independently of stored line order or creation order.
The ordinary point, line, contour and local-handle branches must match the source-proven profile.
Other geometry arrays, construction entities, external/group/name ownership, derived geometry, dimensions, relations, patterns and populated auxiliary managers remain unqualified.
Additional reference points, multiple rings and 3D sketch state retain the legacy projection.
The reader does not infer a rectangle, convexity or a missing edge from coordinates.

Only an admitted typed ring clears false heuristic sketch dimensions/constraints; its typed dimension and relation owners have been verified empty.
Unqualified sketches preserve the previous geometry and constraints.
Existing circle binding runs outside the admitted line path.
Bounds for the admitted ring use every actual vertex through the existing support-plane transform and typed extrusion depth.
Neither synthetic marker offsets nor a bounding-box-only repair is used.

The public `typed_geometry_projection` flag now includes admitted line loops, with explicit `line_loop_profiles` and semantic-field names.
`full_linked_graph`, `typed_assembly_mates` and `public_writer_qualified` remain false in this part-reader evidence.
This slice makes no general writer, new native acceptance or hidden-case claim.

## Verification

[The sanitized receipt](../measurements/2026/TypedLineLoopsSdk01.json) binds the final copied source closure and 40 fresh child processes.
Three independent neutral triangle, concave stepped and clockwise polygon requests each pass two deterministic guarded builds with zero runtime input reads, followed by public SDK reading.
All endpoints, permanent IDs, closed loops, empty relation scope, honest provenance and independently computed prism bounds agree.
Serialized negative controls for an incorrect handle, invalid endpoint, construction line, duplicate permanent marker and populated relation owner stay on the legacy path.
An extended-width encoding, a nontrivial stored-row permutation and independently sparse creation/permanent IDs are read through complete containers.
The explicit extended encoding exercises the decoder's selected branches; it is not new vendor qualification of nonminimal index encoding or a high-cardinality claim.

The same replay retains the previous public blind graph, default/custom system trees, authored folder order, version-18000 model, dimensioned rectangle, annulus, native-saved radial drives and older mixed circle/rectangle sketch.
The four disclosed Native02/Native03 Skew and Step inputs each pass a separate public-reader process, exact typed Resolved byte round-trip and unchanged-input check.
Native03's independent native lifecycle result is SHA-256 `8ca7b13b7bd69f916655539fa08d1df4d836c6c551f218b745e538b84b9bfc0c`.
It is prior oracle evidence, not a native run performed by this task.

The initial copied-source process replay also passed 40 processes; its source/result digests are retained in the receipt.
Its first steering pass rejected naming and declaration-size violations.
The final source-only replay follows mechanical naming/decomposition repairs and passes steering, Ruff, strict Mypy and Pyright, plus the donor scan.
The [research runner](../../tooling/sw2026/InspectTypedLineLoops.py) repeats the process checks and can additionally consume a private explicit disclosed-case job.
