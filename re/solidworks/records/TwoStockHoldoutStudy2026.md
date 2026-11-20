# Independent two-stock part writer comparison

The [source lock](../v2026/heldout/TwoStockWriterSourceLock01.json) pins two independent SOLIDWORKS 2026 SP05.2 native sources before implementation. The [first evaluation](../measurements/2026/TwoStockWriterHoldoutNative01.json) freezes writer `6fc230fb31c3195ff16da5327d4a872f51e49290` before exporting the two neutral authoring requests. Separate guarded processes reproduced both generated archives twice and opened both through the normal strict SDK reader with two analytic solids. The source file bytes stayed in guest custody. Each output was generated solely from its neutral input.

Four fresh native candidate launches opened and rebuilt cleanly, preserved the selected cut through a real edit of the unrelated stock, and reopened the edited native save without errors or warnings. Both controls passed with executable build `34.5.2.0604`. The six native comparisons passed all 144 checks for the two driving depths, per-body volume, area, centre and bounds. The six authored sketch and extrusion rows had the same types, order and parents. The signed frames and selected scope matched.

The full 29-row native tree differed at two names in every comparison. The evaluator supplied `stock:1:plane` and `stock:2:plane` as neutral labels for the fixed supports. The generated archives preserved those labels. The original independent author selected the predeclared `Front Plane` and `Right Plane` names. The comparison retains both differences and the first run qualifies zero cases. [Tree diagnosis](../../tooling/sw2026/throughsource/twostockgraph/CompareHeldoutStockTree01.py) · [Original authoring labels](../../tooling/sw2026/ThroughAllSourcePlan.py)

## Controlled recheck with the authored datum names

The corrected evaluator loaded the canonical datum labels from the original authoring tool and required its source digest to match both the pre-writer repository revision and the native control's pinned tool manifest. It verified the same two sealed authoring-request digests and the exact production source tree `93f0ef018a2e403a5cf98ba2d832a2db16b362fa` from writer `6fc230fb31c3195ff16da5327d4a872f51e49290`. The same strict comparison ran in a separate controlled lifecycle with fresh candidate and control processes. [Corrected evaluator](../../tooling/sw2026/throughsource/twostockgraph/EvaluateTwoStockHoldout01.py) · [Datum-label gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Model/Presentation/NativeDatumLabels.md)

| Pre-writer lock | Generated size | Open, edit, save and fresh reopen | Full native tree parity | Numeric checks |
| --- | ---: | --- | --- | ---: |
| A | 8,641 bytes | Passed | All 29 rows across three snapshots | 72 |
| B | 8,647 bytes | Passed | All 29 rows across three snapshots | 72 |

Both native controls passed with executable SHA-256 `3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`. Four guarded generations and two strict SDK reads reported zero external accesses. The generated cold documents preserve both solids and the selected Front cut. Both source hashes stayed intact. This recheck qualifies the original two locks for this neutral writer profile. It adds zero new source locks and zero FCStd conversions. The first mismatch remains linked above. [Corrected native receipt](../measurements/2026/TwoStockWriterHoldoutNative02.json)

Combined receipt SHA-256 is `6b39921b4959e3662f886def026c55240227f8aab37d3246206bcf02ab8cbb7a`.

## Exact saved-source SDK reads

The four archived native inputs also pass strict SDK reading on the same pinned source tree. Each independent original and its generated, edited, native-saved derivative recovers two editable extrusion owners, a depthless through cut and two physically bound B-rep bodies. All eight driving values match the measured COM values. The typed SDK history contains 30 rows on each original and 31 on each edited native derivative. The separate native application tree comparison retains all 29 visible rows. [Saved-source receipt](../measurements/2026/TwoStockHeldoutSavedRead01.json)

The deterministic research CLI verifies Git-owned assets. For these VM-private files, the transport verified the four exact native record digests and passed the bytes only to isolated ordinary SDK read processes on stdin. The guarded reader performed zero runtime data-file reads. The readback supplies no additional native or held-out acceptance credit. [Readback procedure](../../tooling/sw2026/throughsource/twostockgraph/AuditTwoStockSavedSources01.py)
