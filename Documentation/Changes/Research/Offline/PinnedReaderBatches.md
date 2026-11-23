# Batch pinned research readers

Fusion and SOLIDWORKS stream pinned blobs through one Git process per decode run.
Each request still verifies the Git object ID, type, size, SHA-256, and prefix.
The readers retain per-asset diagnostics and receipt provenance.
Fusion keeps strict refusal and explicit partial fallback.

For SOLIDWORKS, use `kit research --offline --root CHECKOUT solidworks --batch` with repeated `--asset` and an unused `--output`.
The batch shares the pinned tree, SDK source verification, and reader imports.
It publishes one ordered summary and one document and receipt directory per part.
It accepts 1–1000 distinct assets and up to 4 GiB of documents and receipts.
An invalid pin or strict decode failure removes staged batch artifacts.
The singleton command keeps its two-file output and existing receipt contract.
Without `--offline`, the existing native verification procedure checks the published parts in request order.
The feature inventory session decodes the 58 SOLIDWORKS parts in eight batches, with up to four batches in progress.
The session preserves the existing `Solidworks/<path-sha256>` directories and sorted inventory.
When the selected audit source lacks batch support, the session uses singleton decoding.

See [run deterministic research](../../../Tasks/ResearchCommandLine.md#decode-committed-inputs).
The [legacy asset selection gotcha](../../../Gotchas/Research/Offline/LegacySolidWorksAssetSelection.md) explains why the batch flag is explicit.

## Verification

The shared compatibility suite covers ordered SOLIDWORKS artifacts, singleton receipt equality, a failed second pin, and legacy batch rejection.
The Fusion process coverage checks that a strict refusal preserves the later successful control.
Published research artifacts retain unqualified status. Performance and byte comparisons establish CLI compatibility only.
