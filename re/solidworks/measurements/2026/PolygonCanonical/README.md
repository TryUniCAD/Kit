# Canonical-flag polygon native measurements

Full CAD acceptance remains unfinished: all three files change the material-folder name after reopening.
The three named canonical-flag polygon files pass bounded native geometry, visible-view and depth-edit/save/reopen measurements.
Both batches contain healthy independent controls before and after the candidates.
The production adapter remains read-only, and the full CAD goal remains incomplete.

## Exact scope and provenance

The inputs were staged from source revision `4ed467bc94a9e7da00bc9782a603a525250242cd`.
The oracle owner independently compared all three complete files against artifact `14186359068` at head `8d786b341ed291ee7e47fc1964ce7bc64014df04`.
Those files are byte-identical to the staged inputs.
The CI run was `43776684508`, job `133004433464`, using synthetic merge `e04da1ee40d5d6ad91bbd5fa4ad26f444f7693fd`.
The ordered parents and synthetic tree are retained in [provenance](Provenance.json).
The ZIP digest comes from GitHub metadata and was not independently recomputed.
This comparison covers only these three files.

| Generated input     | Bytes | SHA-256                                                            |
| ------------------- | ----: | ------------------------------------------------------------------ |
| H3_scalene.SLDPRT   |  7618 | `557e111c6cc8cdfc72696d2f1b6f0191ef05c17df0746de3c5bf2db88d1b5bc7` |
| H5_irregular.SLDPRT |  7688 | `9b5d2555a200c85c364e1facd09790fea8244fe592caa29bdc71ed3afcfac2b2` |
| H7_irregular.SLDPRT |  7783 | `0a2a5b6f7637cda19b865bd7e057410da9f4baf2b165b7708f8a7d5e4e1c76d2` |

The independent native control SHA-256 is `c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57`.
[SourceManifest4ed.json](SourceManifest4ed.json) and [Artifact8d.json](Artifact8d.json) preserve their historical preparation-stage status fields.
Their pending text predates these completed measurements.
No old material-flag acceptance was transferred to the changed bytes.
The new native batches measure the changed canonical-flag bytes directly.

## Recorded native results

[NativeViewReport.json](NativeViewReport.json) preserves all five visible-view rows.
Each row opened without errors or warnings, rebuilt, retained one body and had clean, unsuppressed features.
The candidates retained 20 features, and the controls retained 19.
All input hashes remained unchanged.
All 90 standard-view arrays contain nine finite coefficients.
Each array was compared with the matching view from both controls before and after selection.
The maximum absolute coefficient difference is `7.888609052210118e-31`, within `1e-12`.
All ten active transforms contain 16 finite numbers.
Selected active rotations match native standard view 7 within `1e-12`.
Initial camera parity remains unestablished.

[EditReport.json](EditReport.json) preserves both controls and all nine candidate baseline/edit/fresh-reopen snapshots.
All nine candidate snapshots have zero open errors, warnings and `whats_wrong` counts, with clean 20-feature trees.
Each depth was multiplied by `1.25`, saved without errors or warnings and reopened in a fresh native process.
The saved-copy SHA-256 matched its fresh-reopen input.
The original candidate hashes remained unchanged.
Across both batches, the records identify 16 distinct native process lifetimes.
The observed executable build is `34.5.2.0604` with SHA-256 `3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`.

| Candidate    | Original depth, m | Edited depth, m |
| ------------ | ----------------: | --------------: |
| H3_scalene   |             0.013 |         0.01625 |
| H5_irregular |             0.007 |         0.00875 |
| H7_irregular |             0.017 |         0.02125 |

## Independent calculations

[Analyze.py](Analyze.py) recomputes the results using only standard-library JSON arithmetic and PNG metadata.
It imports no repository modules and reads no native CAD payloads.
Run `python3 Analyze.py` in this directory to recreate [Analysis.json](Analysis.json).
[BaselineInputs.json](BaselineInputs.json) preserves the preexisting independent neutral models.
Their vertices and requested depths match the unchanged neutral inputs in [EditJob.json](EditJob.json).

Planar area and centroid use the signed shoelace formulas.
Perimeter is the sum of edge lengths.
Volume is planar area times depth, and surface area is twice planar area plus perimeter times depth.
The center of mass is the planar centroid at half depth.
Mass is density times volume.
All 72 independent scalar comparisons across the three view snapshots and nine edit snapshots pass the declared tolerances.

| Metric           |   Maximum absolute error |   Maximum relative error |
| ---------------- | -----------------------: | -----------------------: |
| volume_m3        |  `2.710505431213761e-20` | `4.0307535712750997e-16` |
| surface_area_m2  |  `3.469446951953614e-18` | `3.2159685975360276e-16` |
| mass_kg          |  `2.710505431213761e-20` | `4.0307535712750997e-16` |
| center_of_mass_m | `2.6020852139652106e-18` |  `7.761473939030182e-16` |

The analysis also retains comparisons with the earlier independent baseline and the recorded edit-job expectations.
Every driving-depth readback matches its requested value within `1e-12 m`.
The measured volume changes follow the depth factor within `1e-12`.
[HostReports.json](HostReports.json) records successful terminal parent/transport exits.
Their host lifetimes are `143.836074333 s` for views and `270.617842959 s` for edits.
Generic transport unknown-state flags are retained separately from these document observations.

## Images and names

The oracle owner reported inspecting all ten PNGs.
[RootPosthocVerification.json](RootPosthocVerification.json) records an independent neutral-metric recomputation and image-integrity check.
Its maxima agree with this analysis, and all ten PNG hashes still match the inspected images.
The controls show nonempty cuboids with depth in both captures.
The initial candidate captures show small nonempty front polygons.
All three selected captures show extrusion depth and side faces after standard view 7 and zoom to fit.
[PngConversion.json](PngConversion.json) records the earlier macOS `sips` format-conversion stage.
[ImageManifest.json](ImageManifest.json) binds each unchanged PNG to its native BMP receipt and records the later owner-reported inspection.
Decoded BMP/PNG pixel equality was not independently measured.

| Case          | Initial capture                         | Selected view 7                 |
| ------------- | --------------------------------------- | ------------------------------- |
| ControlBefore | [PNG](images/ControlBefore_initial.png) | [PNG](images/ControlBefore.png) |
| H3_scalene    | [PNG](images/H3_scalene_initial.png)    | [PNG](images/H3_scalene.png)    |
| H5_irregular  | [PNG](images/H5_irregular_initial.png)  | [PNG](images/H5_irregular.png)  |
| H7_irregular  | [PNG](images/H7_irregular_initial.png)  | [PNG](images/H7_irregular.png)  |
| ControlAfter  | [PNG](images/ControlAfter_initial.png)  | [PNG](images/ControlAfter.png)  |

All 20 feature names and types remain equal through each live edit.
Fresh reopening changes only index 12 from `authored material` to `Material <not specified>`.
All 20 feature types and their order remain equal.
Full feature-name preservation is false.
The canonical flag does not repair this [recorded material-folder naming issue](../../../../../Documentation/Gotchas/Conversion/Solidworks/Model/MaterialFolderNameChangesOnSave.md).

## Limits

These results cover three polygon blind-extrusion parts and one depth multiplication by `1.25`.
They establish no sketch driving-dimension edit or broader feature-family, assembly or source-conversion acceptance.
Initial camera parity remains unestablished; full feature-name preservation fails on the material-folder name.
Only complete metadata reports and unchanged PNG evidence are published here.
No native CAD output bytes, proprietary vendor software or sealed curve payloads were copied or inspected during publication.
Metadata arithmetic, hashes and formatting were checked locally.
No product tests, CAD calls or VM commands ran during publication.
