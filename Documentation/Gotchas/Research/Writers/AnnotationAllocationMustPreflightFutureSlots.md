# Annotation allocation must preflight future slots

An unsupported archive allocation should refuse before the serializer changes bytes or maps.
`PartArchiveState` validates its immutable initial map, but `PartArchiveWriter` exposes mutable class and object dictionaries.
An external mutation can occupy a future slot after construction.

The independent Top-annotation probe placed an unrelated object at `next_index + 1` after generating the prior saved views and sketch-block manager.
Before the repair, `WriteAnnotViews(writer, 19000, "*Top", False)` advanced the map and emitted four list bytes before its second allocation raised `ArchiveError`.
The state was already invalid; the probe does not show a failure on a valid constructor input.

Preflight every class and object slot needed by the complete requested emission before writing its first byte.
The bounded serializer now checks the entire future allocation interval.
The [process evidence](../../../../re/solidworks/WriterResearch/Evidence/AnnotationBoundary.json) records unchanged bytes and maps for class and object collisions at each of its three allocation slots.
