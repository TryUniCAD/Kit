# Obsolete queue cleanup

## Behavior

Removing a queue entry can leave its expensive native workflow running.
Those jobs compete with replacement candidates for the same runners.
`QueueCleanup.yml` releases that capacity after a queue branch is deleted or a native queue run is requested or completed.

The cleanup cancels only unfinished, same-repository `merge_group` runs of `.github/workflows/MergeQueue.yml` under `gh-readonly-queue/main/`.
Immediately before cancellation it refreshes the run, reads every page of active queue heads, and requires the exact queue branch to return HTTP 404.
A matching active queue head or any existing branch preserves the run.
Missing queue evidence and API failures stop cleanup without authorizing cancellation.
Manual audits, PR checks, other workflows, forks, and other target branches remain outside its scope.

The operational workflow executes only default-branch code pinned to the triggering default-branch SHA.
It does not load candidate artifacts, caches, scripts, or dependencies.
Its token grants Actions write only to the cleanup job, plus read access for repository and queue metadata.
No acceptance gates or protection settings change.
It is an operational `delete`/`workflow_run` workflow, not a PR or merge-group validation job in the CI allowlist.

## Operation and limitations

No inputs or secrets need configuring.
The workflow becomes active after it reaches the default branch.
The log records cancelled run IDs and preserved runs.
Cleanup uses the supported cancellation endpoint, not force cancellation.
A branch that still exists is deliberately retained even when it might be stale.
Cleanup itself must obtain an Ubuntu runner; it cannot guarantee immediate resource release under saturation.
The live queue concurrency and batching settings still require separate administrator activation as described in [runtime scheduling](QueueRuntimeScheduling.md).

## Verification

The complete test suite includes process-boundary cleanup fixtures covering abandoned and active runs, API failures, pagination, current-run refresh, and excluded workflow identities.
Remote execution and a post-merge queue benchmark remain pending.
No measured speedup is claimed for this change before candidate acceptance and end-to-end timing.
The motivating observations are recorded in [dequeued candidate runs](../../Gotchas/Ci/Scheduling/DequeuedCandidateRuns.md).
