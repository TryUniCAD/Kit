# Stacked workflow backfill

## Expectation

A required workflow already running on `main` will also produce its normal `pull_request` report for a same-repository stacked pull request.

## Actual behavior

The trusted-base aggregate loads its requirements from current `main`, but the pull-request merge tree comes from the pull request's actual base and head. This stacked branch's base predates `FusionCompatibility.yml`. Consequently `CI Agg` required `Fusion archive compatibility`, while no workflow file or matching run existed on the head or merge ref. Waiting for that missing job could not repair it.

This is separate from dynamic `Code Quality`. That managed analysis also has no run for this stacked pull request, and it cannot be restored by adding the unrelated Fusion workflow.

## Workaround

Import the exact pinned upstream workflow and its allowlist registration without changing triggers, checks, permissions, test paths, or security behavior. Byte comparison against the identified `main` commit makes the backfill auditable. The normal pull-request event can then create the missing report, and the existing trusted-base aggregate can consume it without weakening a gate.

Do not synthesize a success status, copy a report from another head, remove the allowlist entry, or claim that this resolves dynamic `Code Quality`. Each required report still needs its own current-revision evidence.

See [the restoration record](../../Changes/StackedFusionCompatibility.md) and [the stacked Code Quality gotcha](StackedCodeQualityReport.md).
