# Detailing edges use downstream kernel identities

The drawing's detailing edge map is keyed by the downstream ID returned from the actual kernel edge attribute. The ordinary drawing feature IDs use a separate allocator. The detailing bucket path also obtains the kernel node ID for a different field. When decoding the map, keep both kernel identifiers and the drawing's persistent node IDs distinct. [Pinned callback and consumer](../../../../../../re/solidworks/records/DrawingDetailingEdgeMap2026.md#native-ownership)
