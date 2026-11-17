# SOLIDWORKS generated prism partition probe

Run `python re/tooling/sw2026/AssemblyPartitionProbe.py <unused external directory>` to stage generated comparative assembly pairs. The research process builds the exact geometry of one dimensioned rectangular child from its live sketch and blind boss. It adds one Parasolid partition to the child in the experimental pair. The ordinary assembly defaults remain unchanged. [Generation, source inventory and validation evidence](../../../../../../re/solidworks/records/PrismPartition2026.md).

The default SDK open produced a validated B-rep in all three indexed assemblies and resolved the same sibling child and real extrusion history as the history-only path. Independent topology, volume, area, centre and extent checks passed. Both read modes exposed a false circle and false radius constraint in the public sketch.

Run `InspectPrismPartitionVariants.py` with the frozen native job to compare the two generated variants at the identical encoded assembly and child paths. The job uses independent geometry targets and known controls. It measures clean open, a driving width edit, synchronized child/parent save and fresh reopen. [Native comparison runner](../../../../../../re/tooling/sw2026/InspectPrismPartitionVariants.py).

In the paired native test, the partition-free child passed its width edit
and synchronized fresh reopen. Adding the generated partition produced warning
32 at the parent open gate. Both controls passed. [Native measurement](../../../../../../re/solidworks/measurements/2026/GeneratedPrismPartitionNative02.json).
