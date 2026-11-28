# Rollback counts follow the owners in each state

The runtime counters in a single-edge fillet's selected partition mark
include nontransmitted pointer-value allocations. The new-node count
counts the actual current rows an undo removes and their hidden allocations.
The deleted-node count counts the prior rows an undo restores and their
own hidden allocations. The two source graphs can have different
attribute inventories.

Count each arm using the allocation state that owns its records. A
pointer field can allocate an array containing one null, while a declared
field can remain unallocated. Keep the runtime copy count separate from
both counts. [Fillet count evidence](../../../../../../../re/solidworks/records/EdgeFilletRollbackCounts2026.md)
