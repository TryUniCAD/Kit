# Parasolid delta handles follow session allocation

Two empty Parasolid histories can have the same mark IDs and different
`delta_key` values. The 2026 E0 source uses key 2 with current mark ID
3, while the historical blank interface uses key 14 with the same mark ID.
The kernel's mark ID and SOLIDWORKS's process-global delta handle have
separate allocators. Raw key comparison therefore depends on prior delta
allocations in the source session.

Supply the current delta handle from the generated history or its allocator
when building a rollback stream. Keep the mark ID as a separate input.
Native blank byte comparisons can use the source's explicit history input
for verification. [Field positions, native allocation, and comparisons](../../../../../../../re/solidworks/records/EmptyPartitionGrammar2026.md)
