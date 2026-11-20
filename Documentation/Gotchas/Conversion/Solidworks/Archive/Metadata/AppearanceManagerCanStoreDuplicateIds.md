# Appearance manager rows may share a material ID

Two SOLIDWORKS 2026 Definition records can carry the same material
ID with different locator casing and mapping values. The native
ordered list preserves both archive vertices. Its lookup map assigns
the later pointer to the same key during restore.

Keep both objects and their wire order in archive round trips.
Treat map precedence as local to the Definition manager.
[Typed native comparison](../../../../../../re/solidworks/records/ConcentricStockChildAppearanceCodec2026.md)
