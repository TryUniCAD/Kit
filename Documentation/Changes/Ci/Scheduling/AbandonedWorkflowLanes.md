# Release abandoned workflow quality lanes

Task: CI-AbandonedWorkflows; owner: Codex; scope: cleanup of abandoned native queue workflow families.
Dependency: the existing trusted cleanup workflow and queue identity checks.
Delivery: this PR. Exit: current-head CI and configured approval, then separately verified queue acceptance.

## Behavior

The cleanup enumerates repository merge-group runs instead of only `MergeQueue.yml` runs.
Cancellation remains limited to `MergeQueue.yml` and `WorkflowQuality.yml`.
Every run still needs matching repository identities, an eligible synthetic branch name, an unfinished status, and a valid SHA.
The SHA must be absent from the complete active queue inventory.
The synthetic branch must return HTTP 404, and the current PR queue entry must be absent or reference another candidate.
Existing refs, active candidates, manual audits, unknown workflow paths, forks, and uncertain API responses remain protected.

The existing process-boundary suite exercises all cleanup cases against both allowed workflow families.
It remains part of the complete shared merge-queue suite.
No new runner, workflow, security exclusion, or acceptance bypass is added.

## Observed blocker and recovery

[Workflow quality run 45384862770](https://github.com/TryUniCAD/Kit/actions/runs/45384862770) was created at 11:30 UTC on 24 November 2026.
It still executed old candidate work after 13:55 UTC.
Six additional obsolete workflow-quality runs remained pending.
The live queue contained only PR 285 candidate `640378100f7bfb0af414829042cd19235a718623`.
All seven old synthetic branches returned HTTP 404, and none of their SHAs matched the active candidate.
Targeted cancellation requests released those abandoned runs while preserving the current candidate.
Fresh Windows shards subsequently started on the current candidate.
Cancellation request success alone is not evidence that a job stopped; read back each run outcome.

The former cleanup excluded these runs because it queried only `MergeQueue.yml` and rejected every other workflow path.
[The gotcha](../../../Gotchas/Ci/Scheduling/AbandonedWorkflowQualityRuns.md) records that boundary.
Formatting and diff checks are the local validation.
Remote policy execution, configured approval, and acceptance remain pending at publication.
Live queue-setting changes remain blocked by the separate administration-connection issue recorded in PR 285.

## Review hardening

The workflow list is filtered against the shared two-path allowlist before any per-run refetch.
The fresh response still passes every independent cancellation check.
A process case includes 999 unrelated workflow rows and rejects any attempt to refetch them.
Queued, pending, waiting, and requested fixtures appear only in their matching discovery queries.
Removing one of those queries therefore fails the corresponding process case.

The flood fixture retains its eligible target within the API’s 1,000-result filtered-search limit.
A separate listed-path value admits the workflow case to refetch, where its fresh unsupported path must still prevent cancellation.
