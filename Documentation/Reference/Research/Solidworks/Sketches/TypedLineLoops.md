# Ordinary typed line-loop reading

`open_document` automatically uses the linked typed `sgSketch` arrays for a qualified ordinary polygon or dimensioned rectangle in a version-19000 SOLIDWORKS part.
The public sketch contains one line per actual line row and one closed profile derived from exact endpoint and incident-handle ownership.
Coordinates are millimetres; native source positions remain available in the point metadata in metres.

Line IDs use the real profile ID and line permanent marker:
`sldprt:sketch:<profile-id>:line:<permanent-marker>`.
Array order, creation IDs, permanent markers and archive-map indices remain separate domains.
Per-entity `typed_archive_owner` records the real sketch object, embedded array and row index.
Its provenance is an owner span rather than an invented line-field offset.
`native_point_rows` retains owned vertex state and the real tagged incident-line handles.

An unconstrained polygon has one connected ordinary line ring and empty dimension and relation collections.
A dimensioned rectangle adds two actual point-distance drivers and four horizontal or vertical relations.
The reader follows each native handle to its actual owned line or endpoint and derives the entity reference counts from those relations. [Typed rectangle dimensions](../../../../Changes/Solidworks/Inspection/Profiles/SolidworksTypedRectangleDimensions.md)

Mixed curves, construction helpers, external reference points, multiple loops and older archives use their existing readers.

`solidworks.typed_resolved_semantics` exposes admitted profile IDs under `line_loop_profiles`, identifies typed dimensioned profiles under `line_dimension_profiles` and sets `typed_geometry_projection` for this bounded geometry.

See the [native field record](../../../../../re/solidworks/records/TypedLineLoops2026.md), [source/process receipt](../../../../../re/solidworks/measurements/2026/TypedLineLoopsSdk01.json), [change entry](../../../../Changes/Solidworks/Inspection/Profiles/SolidworksTypedLineLoopRead.md) and [marker-boundary gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Resolved/PolygonMarkersCanOverreadFeatureBoundaries.md).
