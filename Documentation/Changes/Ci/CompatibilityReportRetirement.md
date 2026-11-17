# Prepare compatibility reports for retirement

## Behavior

The trusted-base CI aggregate permits the absence of the dedicated Fusion compatibility workflow.
Every reported compatibility job and workflow must still succeed.
The existing workflow continues to run until the follow-up PR removes it.

This transition lets the follow-up move compatibility coverage entirely into the merge queue's complete test suite.
The aggregate reads its allowlist from the base revision, so the transition must reach that base first.

## Verification

The existing subprocess cases retain failure coverage for both CLI groups in PR and merge-group aggregation.
A new subprocess case removes the compatibility workflow and its reports from the GitHub response fixture.
It verifies that the aggregate can finish after retirement.
Remote PR checks provide execution evidence. No local tests were run.

See the [trusted-base aggregation guidance](../../Gotchas/Ci/TrustedBaseAggregation.md) and [queue guide](../../../MergeQueue.md).
