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

The public offline CLI benchmark compared base `14570404846c8aa1f90b02e68d6f70a419719ca7` with reader revision `654f00108c3e151c28b5e3e84eb48bd2ff7f9f2a`.
Both used corpus revision `74a0bc353421c25f7a6c539897baadf593a05766` and the same SDK source digest.
The host ran Windows 11 build 26200, Python 3.14.6, and Git 2.53.0.windows.2.
Each comparison used one warm-up pair and five measured pairs in alternating order.

| Offline workload | Base median | Batch median | Byte comparison |
| ---------------- | ----------- | ------------ | --------------- |
| Eight Fusion parts with `--allow-partial` | 16.93 s | 17.01 s | All eight documents matched. One decoded strictly and seven used partial fallback. |
| Three SOLIDWORKS parts with default configuration | 37.20 s across three singleton calls | 17.97 s | All three documents matched, including two reserved parts. |

Fusion used one blob process in place of sixteen for the eight-part workload.
Its median wall time stayed within one percent of baseline.
Separate strict and partial-enabled Fusion runs both retained the F3Z holdout refusal and exit status `3`.
The SOLIDWORKS control's receipt matched byte for byte between candidate singleton and batch runs.
The benchmark verified each revision-bound receipt fingerprint and compared its remaining fields across revisions.
Separate public CLI checks rejected a tampered second pin in both formats without publishing staged artifacts.
The historical checkout rejected `--batch` before publication.
A two-part feature inventory chunk retained request order and published both parts at their existing paths.

| Control neutral document | SHA-256 |
| ------------------------ | ------- |
| `ordinary_rectangle_control.f3d` | `15e49b5f267f2327fd7b69dd975038d9bfa0c25eace57f0a2bcec698e3175825` |
| `example.SLDPRT` | `c30d13ac88073f1497606cf2cacbe7b8c5e88816c4bccce560f28476f9e75eb7` |

The tests cover selected files on one host. The full feature inventory session and cold-cache timings were outside the benchmark.
Published research artifacts retain unqualified status. Performance and byte comparisons establish CLI compatibility only.
