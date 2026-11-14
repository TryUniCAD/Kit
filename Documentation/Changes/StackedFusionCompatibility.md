# Stacked Fusion compatibility restoration

## Behavior and usage

This change restores `FusionCompatibility.yml` and its `Fusion archive compatibility` allowlist entry on the stacked SOLIDWORKS branch. The workflow was added on `main` after this branch's base was created, so the trusted-base aggregate required a report that the branch could not produce.

The imported workflow retains every upstream trigger and check. It runs for `pull_request` and `merge_group`, plus pushes to `main`, and preserves the native schema-provenance check and complete Fusion document, entity, material, geometry, drawing, mesh, container, corpus, bundle, link, and API archive suites. Nothing is skipped, marked optional, or made non-blocking. Actions remain pinned to immutable commits and the runner remains `ubuntu-24.04`.

No manual dispatch event, repository setting, reviewer, protection, or merge action is added. The workflow participates through the existing `CI Agg` report and the native merge queue.

## Limitations

This repairs only the missing Fusion report. It does not manufacture or replace the independently required dynamic `Code Quality` analysis for this stacked pull request. It also does not change the SOLIDWORKS native feature scope, merge the dependent pull requests, or claim merge-queue acceptance before a candidate runs.

## Verification evidence

The workflow and allowlist were compared byte-for-byte with `main` at `2c6a5e9dbc0c46d165fd2de91119f9407d93ed44`; both `cmp` commands returned zero. Their SHA-256 values are:

- `FusionCompatibility.yml`: `4d6f52c3c7bd10d7b3daf48872909d3e64b1c3e379167130c112f325c8219a44`
- `CiAllowlist.cjs`: `e96a4313d0494f948aecaf83d16abb911c6f43d6a0e9757e013e80a247a0013c`

Execution evidence must come from the required `Fusion archive compatibility` job and `CI Agg` on the published head. No early pass is claimed from the byte-identical import alone. The remaining dynamic-analysis blocker is recorded in [the stacked Code Quality gotcha](../Gotchas/Ci/StackedCodeQualityReport.md), and the workflow-reporting behavior is recorded in [the stacked workflow backfill gotcha](../Gotchas/Ci/StackedWorkflowBackfill.md).
