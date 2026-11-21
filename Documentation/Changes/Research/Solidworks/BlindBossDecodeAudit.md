# Offline SOLIDWORKS blind-boss decoding audit

Fresh native acceptance is not established.
No licensed SOLIDWORKS host was available for this run.
The run decoded existing native files and replayed checks against archived application measurements.
It did not author new controls or discover new format rules.

## Source and execution

The [remote audit](https://github.com/TryUniCAD/Kit/actions/runs/44931832555) used source and reporting revision `bd16f35d5a8e5c9440c62f8c4809265ec60dd130`.
All tests ran remotely.
No CAD application or model provider ran in the decoding session.

The [decoded artifact](https://github.com/TryUniCAD/Kit/actions/runs/44931832555/artifacts/14717952175) contains documents, receipts, and `FeatureInventory.json`.
The session inspected 772 pinned inputs and decoded 755 documents.
Seventeen Fusion files were explicitly rejected.
SOLIDWORKS decoded all 58 parts strictly, recovering 748 sketches, 2,482 parameters, and 602 structured feature definitions.
The SOLIDWORKS receipts retain 21,405 unresolved entries.
Every document remains semantically unqualified.

## Bounded feature scope

All eight `CheckSwBoss` cases passed for the existing P03 blind-boss captures.
The cases cover repeated baseline saves, reversed direction, depth, width, height, YZ placement, and inch display units.
All 50 checks under `tests/Research/Inference/Scope/` also passed.
These include plan stability, evidence rejection, grouped rescans, pipeline execution, and resume behavior.

The checks compare public-reader fields, sketch links, parameter provenance, body topology, volume, and centroid.
The [archived native observations](../../../../re/automation/PairedCaptures/P03/solidworks-db1390476325/measurements.json) supply historical measurements.
These observations are not fresh application measurements from this run.

| Case                   | Bodies | Volume (mm³) | Center of mass (mm) |
| ---------------------- | ------ | ------------ | ------------------- |
| Baseline               | 1      | 8,000        | (20, 10, 5)         |
| Reversed direction     | 1      | 8,000        | (20, 10, -5)        |
| Depth edited to 12 mm  | 1      | 9,600        | (20, 10, 6)         |
| Width edited to 41 mm  | 1      | 8,200        | (20.5, 10, 5)       |
| Height edited to 23 mm | 1      | 9,200        | (20, 11.5, 5)       |
| YZ plane               | 1      | 8,000        | (5, 20, 10)         |

Windows platform coverage passed 157 process cases.
macOS platform coverage passed 202 process cases, with 16 explicit skips.
The initial Linux audit reported 6,739 passes, one calibration timeout, and 358 skips across 7,098 collected cases.
The [single shard retry](https://github.com/TryUniCAD/Kit/actions/runs/44931832555/job/136935973155) passed with 1,124 passes and 59 skips.
All current audit jobs report success.
The [summary artifact caveat](../../../Gotchas/Ci/Audits/RerunArtifactReportIdentity.md) explains why the combined summary retains the initial failure.
This manual audit is not merge-group acceptance.

## Repository promotion

The decoding run publishes artifacts, not Git commits or production capability changes.
Research documents retain `portable_complete=false`, `semantic_qualification=unverified`, and `native_acceptance=not_established`.
Retained native bytes are evidence, not portable semantics or writer templates.

Record corroborated findings under `re/solidworks/`.
Use the [codec patch procedure](../../../Tasks/ResearchCommandLine.md#export-a-qualified-codec-change) for a reviewed rule and independently measured cases.
Review the generated patch and publish its source changes, regression coverage, and change entry through a normal PR.
Fresh application controls, rebuild, geometry measurements, and dimension editing remain separate acceptance requirements.
SOLIDWORKS remains a read-only production format.
