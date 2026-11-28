# SOLIDWORKS current-schema receive link evidence

The research record now binds the exact Parasolid 37.01.250 current-schema decoder to the native registration offsets for BODY, REGION, SHELL, FACE and EDGE. For valid compatible scalar references, decode and fixup retain the referenced node in that exact slot. The record includes a metadata-only original-image pin verifier.

This narrows the transport question behind generated drawing downstream IDs. Full receive and application-load ordering, initial chain construction and qualification of new drawing output still require native acceptance.

The verifier checks exact original module and function-range hashes. [Source record](../../../../../../re/solidworks/records/ParasolidReceiveChainLinks2026.md) · [Source receipt](../../../../../../re/solidworks/measurements/2026/ParasolidReceiveChainSource01.json) · [Fixup boundary gotcha](../../../../../Gotchas/Conversion/Solidworks/Archive/Partition/Topology/PointerFixupDoesNotQualifyFullReceiveOrder.md)
