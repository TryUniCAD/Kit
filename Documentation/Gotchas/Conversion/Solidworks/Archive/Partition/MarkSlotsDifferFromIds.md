# Parasolid mark slots differ from mark IDs

Code that compares a transmit slot with a logical mark ID can select the wrong
rollback state. In the disclosed L1 boss, slots 177 and 178 reference marks
whose stored IDs are 7 and 3.

Resolve each pointer through the validated delta graph. Use the corresponding
`PMARK.id` for logical comparisons with the world or a native record's mark ID.
[Measured slot and ID pairs](../../../../../../re/solidworks/records/PartitionMarkIds2026.md)
