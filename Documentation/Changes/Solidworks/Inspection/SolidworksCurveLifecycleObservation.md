# Observe bounded native curve lifecycle state

The existing `full` and `sketch` profiles in
`re/tooling/tupni/Solidworks2026.js` now retain bounded arc records, detailed point
records and independent sketch creation/marker counters. The same existing
serializer, whole-update and coordinate-commit hooks capture before/after state;
this addition introduces no new native hook address.

Arc records include endpoint and centre indices, orientation, topology fields,
creation IDs, permanent markers and constraint status. Detailed point records
include position, point type, role/centre use counts and their corresponding
IDs/status. Line records retain the same ID and status observations. The
arc's auxiliary `fe0/fe4/fe8/fec` references retain offset-based raw labels;
their absent `-2` state does not establish positive-value array namespaces. The
[curve construction ledger](../../../../re/solidworks/records/CurvedSketchConstruction2026.md)
binds those runtime layouts to the pinned 2026 binary.

Detailed point, line and arc snapshots are limited to 512 records per array.
Point active-count scanning keeps its existing 10,000-record limit and reports
detailed-slot completeness separately. An out-of-range count, null container or
failed memory read remains explicit incomplete/error evidence. Never treat an
empty detailed list from an incomplete scan as an empty sketch.
An error preserves the known array/data/count, completed earlier slots, scanned
count and failing index. Point active counts from a partial scan remain separate
from a complete active count. Completeness is explicitly false on every failed
read.

Use the existing hash-verified observation runner, exact x64 realm and original
controls around independent training authoring. Keep vendor-saved held-out source
files unavailable to this detailed inspection. Training snapshots and generated
candidate diagnostics do not replace uninstrumented held-out acceptance.
The [marker placement record](../../../../re/solidworks/records/CircleMarkerPlacement2026.md)
identifies the construction/rebuild distinctions that the next training run must
measure. IDs, archive references, role counts and point-array indices remain
separate namespaces.

Verification for this change was local JavaScript syntax checking and scoped
diff inspection. No native capture or local repository tests were run. Memory
layout evidence is static; curve solver state, final counters and generated
output acceptance remain unverified until the controlled owner run.
