# SOLIDWORKS assembly display list composition

A research composer accepts a selected configuration and ordered display
states with explicit visibility for two generated assembly occurrences. The
shared assembly tree supplies their persistent IDs and XML order. The
composer allocates the list and leaf IDs from the current tree and updates
the root object count.

Four guarded builds on two different allocator layouts preserve their
authored names and visibility. Only `COMPINSTANCETREE` changes. The original
tree is recovered exactly after removing the generated list and restoring its
count. All seven malformed requests refuse, with zero construction file
reads. The SDK's raw XML inspection recovers the mixed states. Native
`VisualStates` writing and the corresponding lifecycle remain open.

[Construction record](../../../../../re/solidworks/records/ConcentricDisplayTreeComposition2026.md)
· [Guarded receipt](../../../../../re/solidworks/measurements/2026/ConcentricDisplayTreeComposition01.json)
