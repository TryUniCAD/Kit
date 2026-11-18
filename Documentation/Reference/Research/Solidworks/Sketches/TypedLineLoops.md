# Ordinary typed line-loop reading

`open_document` automatically uses the linked typed `sgSketch` arrays for a qualified ordinary unconstrained polygon in a version-19000 SOLIDWORKS part.
The public sketch contains one line per actual line row and one closed profile derived from exact endpoint and incident-handle ownership.
Coordinates are millimetres; native source positions remain available in the point metadata in metres.

Line IDs use the real profile ID and line permanent marker:
`sldprt:sketch:<profile-id>:line:<permanent-marker>`.
Array order, creation IDs, permanent markers and archive-map indices remain separate domains.
Per-entity `typed_archive_owner` records the real sketch object, embedded array and row index.
Its provenance is an owner span rather than an invented line-field offset.
`native_point_rows` retains owned vertex state and the real tagged incident-line handles.

The reader requires one connected ordinary line ring with no dimensions, relations, patterns, additional geometry or unmodeled ownership.
Unsupported states keep their existing geometry and constraints.
This includes mixed curves, construction helpers, extra external reference points, multiple loops and older archives.
Existing circle and dimensioned rectangle support is preserved through its established paths.

`solidworks.typed_resolved_semantics` exposes admitted profile IDs under `line_loop_profiles` and sets `typed_geometry_projection` for this bounded geometry.
It does not claim a complete linked graph or enable a writer.

See the [native field record](../../../../../re/solidworks/records/TypedLineLoops2026.md), [source/process receipt](../../../../../re/solidworks/measurements/2026/TypedLineLoopsSdk01.json), [change entry](../../../../Changes/Solidworks/Inspection/Profiles/SolidworksTypedLineLoopRead.md) and [marker-boundary gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Resolved/PolygonMarkersCanOverreadFeatureBoundaries.md).
