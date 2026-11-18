# Populated ghost-body records in SOLIDWORKS configurations

The version-19000 SDK Config codec now reads and writes populated
ghost-body manager rows. Each row has four native integer fields,
a counted identifier array, a conditional object tag and a counted
point array. The existing configuration reader uses the actual
records and object map when it opens the linked Resolved stream.

The original and two independently edited native corner rectangles
now round-trip their complete Config and Resolved streams through the
SDK alone. All six streams and both maps match. The disclosed rows
contain an identifier and no optional object or points. The pinned
2026 binary establishes the conditional object's presence rule and the
point-array field order.

The [field and evidence record](../../../../re/solidworks/records/SdkGhostBodyConfig2026.md)
links the exact checks and archive scope.
