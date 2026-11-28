# Ordinary polygon geometry construction

The SDK adds a typed constructor for an ordinary local closed polygon sketch.
It creates fresh point, line, adjacency-handle and sketch-manager owners through the shared archive object model.
Creation IDs, permanent markers, endpoint indices and collection lengths follow the actual ordered ring.

`PolygonInput` takes local XY coordinates in metres and archive version 19000.
It rejects duplicate vertices, invalid coordinates, zero area, overlapping adjacent edges and nonadjacent contact or intersections.
The validation preserves authored order and uses exact arithmetic on the emitted binary64 coordinates.
The ten-million-vertex bound follows the SDK repetition policy.

Pass an allocated ordinary `moProfileFeature_c` to `MakePolygon`.
The caller supplies its actual component-plane wrapper and complete model-to-sketch frame.
Attach the returned `SketchValue` to the profile's `pd_f80` field.
The returned point and line orders retain the actual constructed owners.
Create a new graph when topology changes.

The constructor covers an unconstrained local ring.
It does not create source dimensions, relations, an origin or a complete part.
Constructor solver states remain separate from measured saved-state behavior.
No public SOLIDWORKS writer is enabled.
The code imports no research module or CAD runtime and reads no file.

The [construction ledger](../../../../re/solidworks/records/SdkPolygonConstruction2026.md) records every field rule and remaining ownership boundary.
See the [typed-field boundary](../../../Gotchas/Conversion/Solidworks/Archive/Construction/PlainArchiveNodesUseTypedFields.md)
and [transform direction](../../../Gotchas/Conversion/Solidworks/Archive/ProfileTransformStoresModelToSketch.md) before integration.
The [archive-context boundary](../../../Gotchas/Conversion/Solidworks/Archive/Construction/SketchBacklinksDependOnArchiveContext.md)
distinguishes constructor backlinks from serialized ownership references.

All forty normal source and process-test files pass formatting, lint, typing and steering checks.
Both research process scripts pass syntax checks.
The first frozen four- and seven-sided guarded builds and build assertions passed.
Separate preparation exposed a checker assumption about an omitted runtime backlink.
The corrected checker follows serialized profile, plane-component and model aliases.
The next run exposed compact handle indices without a full extension field.
The checker now validates compact and extended handle and endpoint forms from their actual wire fields.
See the [compact-index boundary](../../../Gotchas/Conversion/Solidworks/Archive/Construction/CompactSketchIndicesOmitExtendedFields.md).
The corrected frozen process passes both independent build/prepare pairs and the permanent process regression.
The captured runs pass ten fresh-graph stream comparisons and ten separate preparation byte comparisons.
They reject twenty-eight malformed cases and report zero runtime input-file reads.
The resolved stream grows from 14,064 to 14,826 bytes with the authored topology.
The [sanitized receipt](../../../../re/solidworks/measurements/2026/SdkPolygonConstruction01.json) binds all forty-two executable sources and exact results.
The two cases exercise compact indices; no new extended-width witness is claimed.
Native acceptance and held-out qualification remain pending for this SDK source.
