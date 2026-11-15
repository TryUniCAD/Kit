# SOLIDWORKS 2026 local curve and radial construction rules

The [curve construction ledger](../../../re/solidworks/records/CurvedSketchConstruction2026.md)
now records complete static control-flow bounds for the local external-reference
scanner and the separate inter-component reference predicate. Valid local
points, lines and arcs with the stated null external references and empty
auxiliary collections compute the classified local results. The normal native
update computes sketch `f188=0` from the second predicate.

The radial construction record derives radius and diameter parameter values
from geometry and native option rules. It identifies the owned parameter,
display-handle links and nonnull invalid second handle. This is constructor and
wire knowledge, not an implemented curve writer.

The [circle marker lifecycle gotcha](../../Gotchas/Conversion/Solidworks/Model/CircleMarkersSkipOrdinaryPointUpdates.md)
records why polygon point-update rules cannot establish final circle marker
coordinates. The native predicate and solver skip branch are classified;
the [marker placement record](../../../re/solidworks/records/CircleMarkerPlacement2026.md)
derives the native angular search and distinct creation/rebuild fallbacks.
The [index-specific collision gotcha](../../Gotchas/Conversion/Solidworks/Model/CircleMarkerCollisionsUseIndexSpecificBounds.md)
records the new index's half-open XY box and the legacy index's closed XY box.
The predicate excludes type-two markers and compares eligible ordinary points
in the local sketch frame. Native engine selection and complete first-solve
acceptance remain separate obligations.

For full-circle radius and diameter displays, the native witness engine's
guarded false-result branch explicitly assigns both witness points zero and
skips its plane transforms. The ledger records that intermediate rule separately
from constructor zero seeds and unverified later presentation mutations. It does
not establish final saved values or acceptance of an emitted dimension.

Use these records to extend the shared graph only after locking the new native
source family. The bounded reference results do not validate arbitrary
constraints, display state, IDs, contours or extrusion geometry. Preserve every
stated owner, index and empty-collection condition. No generated circle or arc
is accepted and no production capability is enabled.

Verification used hash-bound 2026 DLL bytes, PE function extents, existing private
analysis and direct instruction inspection. No native held-out stream was read,
no CAD application was launched or attached, and no local tests ran for this
static extension. Native solve, edit and geometry acceptance remain pending.

The earlier profile ledger's framework image base was also corrected against
the pinned PE header. Its constructor address and line-width rules were
independently reverified and remain unchanged. The
[preferred-base gotcha](../../Gotchas/Conversion/Solidworks/Tracing/PreferredBasesMustMatchPinnedImages.md)
and linked evidence retain the exact distinction. Older polygon/profile/visual
status text now points to the actual restricted native measurement record.
