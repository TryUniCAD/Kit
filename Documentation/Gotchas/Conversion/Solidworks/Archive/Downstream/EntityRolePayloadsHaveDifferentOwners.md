# Embedded entity roles have different producers

The embedded downstream record stores a role map, an edge-ID vector, a face hint and a vertex endpoint pair. The vertex and edge paths populate their own fields. The candidate pointer vector exists only at runtime.

The initial face constructor searches only rows already inserted, so its own role 0 can appear during a later replacement. A body representative gets role 0 on a separate face copy. Preserve the type-specific fields when reading or constructing each branch. [Stored face state](../../../../../../re/solidworks/records/DownstreamStoredFaceState2026.md)
