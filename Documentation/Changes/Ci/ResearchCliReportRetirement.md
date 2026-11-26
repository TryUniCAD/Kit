# Prepare the Linux research CLI report for retirement

## Behavior

The trusted-base CI aggregate permits the absence of the `Research CLI compatibility` report from `Workflow quality`.
A reported `Research CLI compatibility` job must still succeed on merge-group candidates; a failure, cancellation, timeout or skip still fails the aggregate.
The job itself keeps running until the follow-up PR removes it.

The follow-up deletes the serial Linux job because the merge queue's complete test suite already collects and runs every `tests/CliResearch` case.
The aggregate reads its allowlist from the base revision, so this transition must reach `main` before the follow-up's queue candidate.
Enqueue the follow-up only after this change has merged.

`RetiringJobs` in `.github/scripts/CiAllowlist.cjs` holds the names that may be absent.
The follow-up removes the entry together with the job and its phase assignment.
The Windows research CLI jobs are unchanged.

## Verification

A new subprocess case removes the `Research CLI compatibility` check from the merge-group fixture and verifies that the aggregate passes.
The existing queue cases still fail when that check reports `failure`, `neutral`, `skipped`, `cancelled` or `timed_out`.
Remote PR checks provide execution evidence.

See the [trusted-base aggregation guidance](../../Gotchas/Ci/TrustedBaseAggregation.md), the earlier [compatibility report transition](CompatibilityReportRetirement.md) and the [queue guide](../../../MergeQueue.md).
