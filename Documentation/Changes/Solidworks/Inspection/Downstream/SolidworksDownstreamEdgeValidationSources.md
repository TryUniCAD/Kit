# Downstream edge validation source checkpoint

PR #121 adds exact-build source ownership for the ordinary edge's initial mode trial and post-insert repair. The [record](../../../../../re/solidworks/records/DownstreamEdgeValidation2026.md) separates actual topology validation, runtime cache prerequisites, original/anti key text, earlier-row reconciliation and same-ID current-row fallback.

For the explicitly bounded collision-free ordinary prism, the supplied mode-1 reference retains its incoming flags and cache fields through these validators. No `fe8` clearing rule is invented. The broader collision helper can replace an earlier row while preserving that row's allocated ID. Classification 2 means two-or-more common edges, and an edge anti key swaps different ID slots from a face anti key.

The [source receipt](../../../../../re/solidworks/measurements/2026/DownstreamEdgeValidationSource01.json) checks 32 complete function owners and 74 intervals, three concrete virtual slots and ten import identities across two pinned originals. No CAD input or product test ran; no generated downstream/native acceptance is claimed.

After staging, run the source-only checker against licensed originals and an unused output path:

```sh
python3 -B re/tooling/sw2026/downstream/VerifyEdgeValidationSources.py --bin-directory /path/to/licensed/pinned/bin --record re/solidworks/records/DownstreamEdgeValidation2026.json --output /unused/EdgeValidationSources.json
```

The addition changes no production behavior. Positive-fin selection, constructor fields, live handles, collisions, alternate contexts, helper teardown and final native qualification remain independently owned obligations. [Saturated classification](../../../../Gotchas/Conversion/Solidworks/Archive/Downstream/Edges/CommonEdgeResultTwoIsSaturated.md) · [Anti-key slots](../../../../Gotchas/Conversion/Solidworks/Archive/Downstream/Edges/EdgeAntiKeyUsesDifferentSlotPairs.md) · [Earlier-row repair](../../../../Gotchas/Conversion/Solidworks/Archive/Downstream/Edges/EdgeRepairCanReplaceEarlierRows.md)
