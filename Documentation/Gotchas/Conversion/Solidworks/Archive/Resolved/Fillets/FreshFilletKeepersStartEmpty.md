# Fresh fillet keepers start empty

The two stored surface IDs and selected-edge alias in an ordinary saved
fillet come from distinct phases. The fresh edge keeper constructs empty
surface and retained-edge collections. The pre-solve reset adds a generic
surface ID from the owning feature. The selected-edge setter keeps its
reference in a separate pending array. The successful result assignment
moves that reference to the persistent array and adds the produced
fillet surface ID.

Keep the pending and persisted aliases separate when modeling a fresh
fillet. Preserve the existing cardinalities when reading the measured
saved profile. [Exact-build construction and assignment evidence](../../../../../../../re/solidworks/records/EdgeFilletResultOwners2026.md)
