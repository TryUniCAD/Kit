# Selected downstream late-edge pass

PR #121 records the exact SOLIDWORKS 2026 late vertex/edge stage for a fresh ordinary rectangular prism. With retained mode-1 references, no original/anti-key collision, an empty pending tree and native option bit 0 clear, the selected stage adds no vertex rows and performs no endpoint-hint repair. These predicates are explicit construction obligations.

The record also distinguishes temporary curve cleanup from late repair and proves that ordinary BEnt store retains `fe8` verbatim and `f70` low32. A cache-clear function name does not establish a zero wire default.

Use the [field and lifecycle ledger](../../../../../re/solidworks/records/DownstreamLateEdgePass2026.md) and its numeric pins to review the selected branch. The [metadata receipt](../../../../../re/solidworks/measurements/2026/DownstreamLateEdgeSource01.json) replays original module/function/window identities only. No SDK, native or held-out process was run; no public codec/writer admission changes. Nested temporary-helper teardown and final save readiness remain open. [Specific gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Downstream/Edges/EdgeCacheBitsAreSerialized.md)
