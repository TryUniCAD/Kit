# Obsolete queue cleanup

## Behavior

Removing a queue entry can leave its expensive native workflow running.
Those jobs compete with replacement candidates for the same runners.
`QueueCleanup.yml` releases that capacity after a queue branch is deleted, with another sweep after updates to `main`.

The cleanup cancels only unfinished, same-repository `merge_group` runs of `.github/workflows/MergeQueue.yml` under `gh-readonly-queue/main/`.
Each sweep reads every page of active queue heads once, avoiding repeated full scans as unfinished runs accumulate.
Before cancellation it refreshes the run, requires the exact queue branch to return HTTP 404, and directly checks its source PR's current queue candidate SHA.
A matching active queue head or any existing branch preserves the run.
The direct PR check preserves a matching candidate or an entry whose candidate identity is unavailable.
A missing source entry or a different valid candidate SHA permits cleanup of the abandoned run.
This releases superseded speculative candidates even while their replacement remains queued.
Unrecognized queue branch naming preserves the run.
Missing queue evidence and API failures stop cleanup without authorizing cancellation.
Manual audits, PR checks, other workflows, forks, and other target branches remain outside its scope.

The operational workflow executes only default-branch code pinned to the triggering default-branch SHA.
It does not load candidate artifacts, caches, scripts, or dependencies.
Its token grants Actions write only to the cleanup job, plus read access for repository and queue metadata.
No acceptance gates or protection settings change.
It is an operational `delete`/`push` workflow, not a PR or merge-group validation job in the CI allowlist.

## Operation and limitations

No inputs or secrets need configuring.
The workflow becomes active after it reaches the default branch.
The log records cancelled run IDs and preserved runs.
Cleanup uses the supported cancellation endpoint, not force cancellation.
A branch that still exists is deliberately retained even when it might be stale.
Cleanup itself must obtain an Ubuntu runner, so it cannot guarantee immediate resource release under saturation.
It does not poll on a schedule or consume runners when the repository is idle.
The live queue concurrency and batching settings still require separate administrator activation as described in [runtime scheduling](QueueRuntimeScheduling.md).

## Verification

Task: obsolete queue runner cleanup, owned by Codex in [PR #268](https://github.com/TryUniCAD/Kit/pull/268).
Scope: native queue resource cleanup; dependency: default-branch rollout.
Exit: current-head PR gates and configured approval, then separately authorized queue acceptance and measured timing.

The complete test suite includes process-boundary cleanup fixtures covering abandoned and active runs, API failures, pagination, current-run refresh, and excluded workflow identities.
Failure scenarios require the expected API error evidence and exact candidate refs so unrelated fixture assertions cannot count as successful failure handling.
Remote execution and a post-merge queue benchmark remain pending.
No measured speedup is claimed for this change before candidate acceptance and end-to-end timing.
The motivating observations are recorded in [dequeued candidate runs](../../Gotchas/Ci/Scheduling/DequeuedCandidateRuns.md).
The implementation retains the security audit by avoiding [workflow completion triggers](../../Gotchas/Ci/Scheduling/WorkflowCompletionTriggers.md).
The [queue entry identity](../../Gotchas/Ci/Scheduling/QueueEntryIdentity.md) check distinguishes a superseded candidate from its still-queued source PR.
