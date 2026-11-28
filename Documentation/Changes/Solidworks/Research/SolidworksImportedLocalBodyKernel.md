# Record SOLIDWORKS imported local-body kernel ownership

The [local BODY audit](../../../../re/solidworks/records/ImportedLocalBodyKernel2026.md)
checks a pinned SOLIDWORKS 2026 SP05.2 imported solid. It uses shared
Parasolid node definitions and wrapper framing to reproduce the raw
transmit and compressed wrapper byte for byte from the typed graph in memory.

The [measurement](../../../../re/solidworks/measurements/2026/ImportedLocalBodyKernel01.json)
checks 172 resident nodes, 27 attributes and 12 shared declarations. The
[definition link gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Partition/LocalBodyDefinitionsCanLinkOutsideTransmit.md)
records twelve nonresident `ATTRIB_DEF.next` pointers that need
further research before fresh construction. The audit grants no
generated output or native writer acceptance credit.
