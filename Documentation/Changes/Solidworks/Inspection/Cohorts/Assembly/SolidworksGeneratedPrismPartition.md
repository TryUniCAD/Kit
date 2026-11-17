# SOLIDWORKS generated prism partition probe

Run `python re/tooling/sw2026/AssemblyPartitionProbe.py <unused external directory>` to stage generated comparative assembly pairs. The research process builds the exact geometry of one dimensioned rectangular child from its live sketch and blind boss. It adds one Parasolid partition to the child in the experimental pair. The ordinary assembly defaults remain unchanged. [Generation, source inventory and validation evidence](../../../../../../re/solidworks/records/PrismPartition2026.md).

The default SDK open produced a validated B-rep in all three indexed assemblies and resolved the same sibling child and real extrusion history as the history-only path. Independent topology, volume, area, centre and extent checks passed. Both read modes exposed a false circle and false radius constraint in the public sketch. The native SOLIDWORKS cache interpretation and synchronized edit/save/reopen still require an oracle comparison.
