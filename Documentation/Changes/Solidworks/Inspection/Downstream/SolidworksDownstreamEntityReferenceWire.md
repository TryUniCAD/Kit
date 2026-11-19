# Downstream entity-reference wire source checkpoint

This research addition records the exact SOLIDWORKS 2026 ordinary direct BEnt, face, edge, vertex, inline entity-ID and embedded downstream body grammar. It distinguishes typed archive pointers from embedded bodies, condition-bit `0x80` face-row omission, and native load normalization. It adds no production codec registration or writer admission.

Use the [field/context record](../../../../../re/solidworks/records/DownstreamEntityReferenceWire2026.md) and numeric JSON when extending the existing materialized reference layouts. The metadata-only verifier takes `--bin-directory`, `--record`, unused `--output`, and optional `--checkout` for metadata verification.

[Actual verification](../../../../../re/solidworks/measurements/2026/DownstreamEntityReferenceSource01.json): four original module identities, 35 complete function entries, 53 source intervals, six runtime descriptors/dispatch cells, four auxiliary descriptors, and three exact SDK source files. Native processes, SDK executions, CAD inputs and held-out reads were all zero. Complete recursive graphs, dynamic representation classes, drawing incident-edge order and nondefault identity generation remain unqualified.

The [vertex identity gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Downstream/VertexReferenceSuffixUsesIncidentEdge.md) and [normalization gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Downstream/EntityReferenceRowsNormalizeOnLoad.md) describe concrete implementation traps. Task `PR121-DownstreamEntityReferenceWire`, owner `configuration_header`, delivery PR #121.
