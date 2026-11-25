# Preserve narrow cylinder snapshot transport

## Behavior

The specialized cylinder snapshot writer preserves four-byte and eight-byte integer framing.
It generates its known cylinder records, then uses the existing width-aware geometry serializer for four-byte framing.
Other header fields retain their existing exact guard. No source archive, template or captured payload supplies writer constants.

## Evidence and qualification

The rim-fillet campaign found seven native sources whose only specialized snapshot-header difference was `IntWidth = 4`.
The generic serializer already supports that width. The original seven refusals remain in the research pack.
The bounded repair is undergoing deterministic complete-model comparison and fresh-process native acceptance.
Post-freeze parameter controls are declared separately from the original observed corpus.
Current qualification receipts will be linked after execution; no complete semantic or cross-format conversion is claimed.

The [feature pack](../../../re/Fusion/RimFilletPack/README.md) records the original boundary and evidence lineage.
