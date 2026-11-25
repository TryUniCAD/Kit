# Preserve narrow cylinder snapshot transport

## Behavior

The specialized cylinder snapshot writer preserves four-byte and eight-byte integer framing.
It generates its known cylinder records, then uses the existing width-aware geometry serializer for four-byte framing.
Other header fields retain their existing exact guard. No source archive, template or captured payload supplies writer constants.

## Evidence and qualification

The rim-fillet campaign found seven native sources whose only specialized snapshot-header difference was `IntWidth = 4`.
The generic serializer already supports that width. The original seven refusals remain in the research pack.
The bounded repair passed 22 complete-model comparisons and corresponding native acceptance checks: 12 original sources, six depth-edited sources and four fresh post-freeze parameter cases.
Post-freeze parameter controls are declared separately from the original observed corpus.
[Qualification receipts](../../../../re/Fusion/RimFilletPack/Qualification/Cases.json) bind each output hash to fresh native measurements or an exact matching prior receipt.
The [audit](../../../../re/Fusion/RimFilletPack/Qualification/Audit.json) verifies geometry, parameters, controls and radius edit/restoration. Six independent depth edits also matched analytical volume increments and restored.
Six whole-archive malformed-header checks preserved an existing destination and the source.
The qualified SDK is `d4b580b5a65229d0f345609592a2b87b0262be9b`; retained source hashes bind later documentation/test commits to that implementation.
Shared compatibility regressions cover all 22 archive cycles, six header guards, source-free construction and strict conversion refusal. They use the existing suite and Windows roster.
No complete semantic or cross-format conversion is claimed.

The [feature pack](../../../../re/Fusion/RimFilletPack/README.md) records the original boundary and evidence lineage.
