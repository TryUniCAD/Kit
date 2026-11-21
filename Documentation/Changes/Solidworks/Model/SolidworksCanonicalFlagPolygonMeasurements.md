# Measure canonical-flag polygons in SOLIDWORKS 2026

The [canonical polygon evidence](../../../../re/solidworks/measurements/2026/PolygonCanonical/README.md) now records controlled native results for the changed material-flag bytes.
The exact three inputs match CI artifact `14186359068` at head `8d786b341ed291ee7e47fc1964ce7bc64014df04`.
The immutable source manifest remains tied to its original `4ed467bc94a9e7da00bc9782a603a525250242cd` preparation stage.
[Provenance](../../../../re/solidworks/measurements/2026/PolygonCanonical/Provenance.json) records the complete-byte comparison and the verified CI synthetic parents and tree.

## Evidence

Both native batches passed their independent controls before and after the candidates.
Five visible-view rows opened cleanly, rebuilt and retained one body each.
All 90 standard-view arrays contain nine finite coefficients and match controls within `1e-12`.
The maximum absolute coefficient difference is `7.888609052210118e-31`.
The oracle owner reported inspecting all ten unchanged published PNGs.
The selected views show extrusion depth and side faces.
Initial camera parity remains unestablished.

All three depth edits multiplied the driving depth by `1.25`, rebuilt, saved cleanly and reopened in fresh processes.
All nine candidate edit snapshots have zero recorded problems and clean 20-feature trees.
Original input hashes remain unchanged.
[Analysis](../../../../re/solidworks/measurements/2026/PolygonCanonical/Analysis.json) derives 72 passing scalar comparisons from the independent neutral polygon inputs.
The maximum absolute center-of-mass error is `2.6020852139652106e-18 m`.
The [independent owner verification](../../../../re/solidworks/measurements/2026/PolygonCanonical/RootPosthocVerification.json) agrees with these maxima and confirms the ten inspected PNG hashes.

## Names and limits

All feature names remain equal through live editing.
Fresh reopening changes only material-folder name index 12 to `Material <not specified>`.
All 20 feature types and their order remain equal.
The canonical flag does not repair the [existing naming issue](../../../Gotchas/Conversion/Solidworks/Model/MaterialFolderNameChangesOnSave.md).
Full feature-name preservation remains false.

These measurements cover three named polygon blind extrusions and one depth-edit/save/reopen operation.
They establish no broader feature-family, assembly, source-conversion or production writer acceptance.
The production adapter remains read-only, and the full CAD goal remains incomplete.
Publication used metadata arithmetic, hashes, formatting and unchanged PNG copies.
No native CAD payloads, product tests, oracle calls or VM commands were used during publication.
