# Ghost manager flags follow partition bodies

The SP05.2 Config-0 ghost manager stores a signed high-nibble flag beside its low 28-bit row count. Inline ghost rows can have an absent geometry-object field while their actual bodies live in the separate configuration GhostPartition. The serializer sets bit 1 and clears bit 0 when that partition reports bodies. The alternate branch sets bit 0 and clears bit 1.

When inspecting a populated manager, resolve the physical ghost partition and the body-owned ghost ID attributes before projecting geometry from the rows. The two ordinary sweep references each have an actual body in that partition even though both rows have `has_f50=0`. [Exact 2026 sweep ownership and flag evidence](../../../../../re/solidworks/records/OrdinarySweepGhostOwnership2026.md)
