# Portable plane intersection axis

Use `interchange.PlaneAxis` or `interchange.history.PlaneAxis` for a finite directed reference axis with two ordered local support selections. Ordinary `CadDocument` JSON and mapping reads preserve the selection roles and verify the segment against the actual plane frames. The `PlaneIntersectionAxis` wire record carries both selection IDs and the start and end points in model-space millimetres.

The [guarded proof](../../../re/solidworks/records/PortablePlaneIntersectionAxis2026.md) covers translated and oblique axes, malformed ownership and geometric contradictions, historical neutral wire and validation, and byte-exact results through the scoped research composer. See the [feature model](../../Reference/Model/Features.md#plane-intersection-axes) for the neutral contract.
