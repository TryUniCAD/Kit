# Allocate coincident mate wrapper IDs in Config-0

The research assembly builder allocates each resolved wrapper's ID
from the containing assembly's next reference counter. It derives the
mate's persistent ID and local endpoint ordinal separately. Repeated
registration preserves the assigned reference IDs.

Both guarded inputs write and decode two named mate wrapper sets and
advance the Config-0 counter to four. The new counter changes exactly
one byte in each original configuration. The retry and invalid-input
controls preserve the graph state. Native qualification of the complete
mate remains open.

[Allocation rule](../../../../../../re/solidworks/records/CoincidentMatePublication2026.md#wrapper-ids-consume-a-separate-counter)
and [process receipt](../../../../../../re/solidworks/measurements/2026/GeneratedPlanarWrapperIds01.json).
