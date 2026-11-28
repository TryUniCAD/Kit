# A child cache can change the assembly open warning

The child opened standalone with warning 32 and zero solids after adding one generated Parasolid partition. An explicit rebuild restored its solid and six extrusion-owned faces. Opening the parent directly with that child also returned warning 32, although the first component inspection already found the solid and a clear rebuild flag. The cache-free child opened cleanly through both routes. The persisted update and geometry counters matched across the two variants.

Measure standalone and referenced loads at the same child path. Record warnings, live stamps, body availability and feature ownership before rebuilding. The standalone result locates this failure during child load or initialization even when the parent exposes a solid. Kernel restore, delta handling, and attachment remain separate possibilities. [Measured comparison](../../../../../re/solidworks/records/PrismPartitionOpen2026.md).
