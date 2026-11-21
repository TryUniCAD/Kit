# SDK assembly history component

Two disclosed SOLIDWORKS 2026 SP05.2 assemblies round-trip all six linked Config-0, ResolvedFeatures and MatesList streams through the typed SDK. The [corpus manifest](../v2026/corpus/assemblies/Manifest.json) records both the native source and equal-width redacted fixture hashes. These are disclosed parser controls.

## Observed archive rule

`Contents/Config-0-ResolvedFeatures` owner `moHistoryCompItemData_c` schema 1 serializes the `moNode_c` base followed by the chain-component pointer at object offset `+0x48`. The pinned `sldmodu.dll` digest is `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Serializer `0x4b645080` calls node-base helper `0x4b645260` and the class uses vtable `0x4ce42360`. XML and resolved dispatch are fieldless. Lightweight dispatch goes to `moNode_c.SerializeLWData`, and the XML flag is true. [Native grammar](AssemblyArchive2026.md#component-history-and-favorites)

The vendor reader sets archive state `+0x8a0` to one while resolving the pointer, then clears it. The SDK restores the previous clear state even if child decoding fails. The writer transfers the pointer through the shared archive map. In the measured graph, the concrete `moChainComponent_c` points back to the inherited assembly and reaches `moReferenceChain_c` and `moExtFeatureList_c` through the existing shared field layouts. The SDK admits those three descriptors and the history owner at schema 1 in the ordinary version-19000 assembly resolved context. [Read-context gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/HistoryComponentReadContext.md)

The field order and concrete classes are confirmed by the native rules and source bytes. The one-way state comes from the native load and store branches. The shared chain fields exercised by these fixtures do not consult that state. The earlier SDK stopped at the history descriptor at byte 635 in both controls.

## Linked archive reproduction

| Control | Config-0 bytes / map count | ResolvedFeatures bytes / map count | MatesList bytes / map count | Mate roots |
| --- | ---: | ---: | ---: | ---: |
| A0 one component | 24,828 / 103 | 5,444 / 172 | 6 / 172 | 0 |
| A1 two components | 25,338 / 108 | 5,500 / 181 | 10,411 / 250 | 3 |

The observer opens the disclosed fixture at its research input boundary and passes the in-memory container to `ReadNativeLink`. Both directions carry the same typed map from configuration through resolved data and mates. The observer checks byte identity, complete typed reports and the identity of each retained history pointer and its referenced graph. The [receipt](../measurements/2026/SdkAssemblyHistoryComponent01.json) binds each stream, fixture, source declaration and codec owner by SHA-256. This evidence covers archive reproduction of the two sources. Held-out conversion, generated assembly output and native rebuild acceptance are outside this measurement.

From the repository root, run the [observer](../../tooling/sw2026/InspectSdkHistoryComponents.py) and compare its output to the receipt.

```sh
PYTHONPATH=src uv run --offline --no-project --python 3.13 python -B re/tooling/sw2026/InspectSdkHistoryComponents.py | diff -u re/solidworks/measurements/2026/SdkAssemblyHistoryComponent01.json -
```
