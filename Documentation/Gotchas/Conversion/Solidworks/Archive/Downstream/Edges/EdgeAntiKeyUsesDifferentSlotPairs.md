# Edge anti keys use different slot pairs

**Expectation:** an edge's anti key can reuse the face reference's slot-1/2 swap.

**Actual behavior:** `moEdgeRef::makeAntiCopy` swaps slots 0/1 and 2/3, preserves slot 4 for a five-slot reference, and rejects other odd counts. An additional actual entity-ID equality branch rewrites anti slots 2/3 to original slot 0 when original slots 2, 3 and 1 are equal. It copies the source cache words into the temporary owner.

**Workaround:** construct anti text from the actual edge transformation and the same source-derived key function. Prove the degeneracy absent before using a simple four-slot pair swap. Face and edge key hashes share their text/polynomial framing but not this transformation.

The [source record](../../../../../../../re/solidworks/records/DownstreamEdgeValidation2026.md) binds the complete native function and field owners. This is source evidence, not native acceptance of an arbitrary edge family.
