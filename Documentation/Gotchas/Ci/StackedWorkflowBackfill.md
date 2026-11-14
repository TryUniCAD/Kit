# Stacked workflow backfill

## Expectation

A required workflow already running on `main` will also produce its normal `pull_request` report for a same-repository stacked pull request, and importing its workflow file alone can restore that report.

## Actual behavior

The trusted-base aggregate loads its requirements from current `main`, but the pull-request merge tree comes from the pull request's actual base and head. This stacked branch's base predates `FusionCompatibility.yml`. Consequently `CI Agg` required `Fusion archive compatibility`, while no workflow file or matching run existed on the head or merge ref.

Importing the byte-identical current workflow and allowlist entry did start the required job on head `baab006d06c69e3a7f57af25135c24c93eb9bc1b`, but it failed immediately because `re/Fusion/Reconstruction/EntityGraph/PromoteCatalog.py` and the Fusion implementation are also absent from the older stacked base. The workflow's later archive tests did not run. A workflow-only backfill cannot supply the missing implementation.

This is separate from dynamic `Code Quality`. That managed analysis also has no run for this stacked pull request and is not restored by the unrelated Fusion workflow.

## Workaround

Do not synthesize a success status, copy a report from another head, skip the missing step, or remove the required workflow from the trusted-base allowlist. A standalone workflow import is insufficient when its checked-in implementation is also missing.

Use a faithful integration of the current base into the task branch so both the workflow and the exact code it validates are present, then let the normal pull-request event produce a real report. That integration must preserve both revisions' behavior and trigger a fresh full validation. Alternatively, wait until the dependent base advances while retaining the visible missing-report blocker.

See [the failed Fusion run](https://github.com/TryUniCAD/Kit/actions/runs/43572884077) and [the stacked Code Quality gotcha](StackedCodeQualityReport.md).
