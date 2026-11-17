# A child cache can change the assembly open warning

The same native assembly opened without warnings with its generated cache-free child and with warning 32 after the child added one generated Parasolid partition. The persisted update and geometry counters were equal in both variants. In the clean lane the runtime child stamp already differed from its persisted counter after open.

Measure standalone and referenced loads at the same child path. Record warning, live stamps, body availability and feature ownership before rebuilding. Matching on-disk stamps distinguish this case from a missed child save and leave cache loading and runtime binding as separate diagnostic paths. [Controlled comparison and follow-up method](../../../../../re/solidworks/records/PrismPartitionOpen2026.md).
