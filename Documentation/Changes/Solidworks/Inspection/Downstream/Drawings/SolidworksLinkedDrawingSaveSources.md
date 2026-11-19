# Linked drawing cache use before save notification

PR #121 records the exact drawing pre-save route through a child's downstream edge cache, the native SaveModelData store gate and the forced externalization of copied drawing references. It adds a source-bound edge-annotation observation protocol and changes no SDK behavior, writer defaults or public admission.

The metadata-only source receipt pins original images, complete source owners, direct calls, imports and concrete virtual cells. The proposed native observer is not implemented or qualified. Root still owns exact wrapper metadata, candidate/control custody, runtime measurements and edit/save/fresh-reopen acceptance. Preserve older property-save failure receipts; later lexical-prefix and linked SDK passes supply the current scope.

[Source record](../../../../../../re/solidworks/records/DownstreamLinkedDrawingSave2026.md) · [Protocol design](../../../../../../re/solidworks/records/DownstreamEdgeAnnotationProtocol2026.json) · [Source receipt](../../../../../../re/solidworks/measurements/2026/DownstreamLinkedDrawingSaveSource01.json) · [Timing gotcha](../../../../../Gotchas/Conversion/Solidworks/Archive/Downstream/Edges/DrawingEdgeLookupPrecedesSaveNotify.md)
