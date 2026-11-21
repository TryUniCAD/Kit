# Edge cache bits are serialized

## Expectation

BEnt flags `0x100/0x200/0x400` describe runtime cache state, so the ordinary serializer will omit or clear them. A late cleanup pass therefore implies zero saved flags and populated endpoint hints.

## Actual behavior

Exact 2026 EdgeRef uses BEnt Serialize directly. Store emits the actual `fe8` word verbatim, including cache bits, and low32 of `f70`. `clearEntCache` masks only the cache-bit group while retaining `f70`, `f18` and `f60/f64`. That clear is an explicit operation, not an automatic wire rule.

The late pending-edge pass returns immediately when the actual pending tree is empty. With native option bit 0 also clear, the fresh orchestrator skips both vertex-allocation paths. It does not invent vertex rows or endpoint hints for every geometrically valid edge.

## Workaround

Derive incoming state and selected call conditions from the actual model and native owners. Preserve the bits that reach the serializer. Do not add a blanket clear or synthesize vertex IDs. Keep later teardown and final save preservation separate until their actual call chain is proved.

[Exact source ledger](../../../../../../../re/solidworks/records/DownstreamLateEdgePass2026.md) · [Metadata-only receipt](../../../../../../../re/solidworks/measurements/2026/DownstreamLateEdgeSource01.json)
