# Superseded breaking-label runs

## Ownership

Task CI metadata label backlog; owner Hoplite; scope is obsolete breaking-label workflow cancellation.
Dependencies are current-metadata label reconciliation and existing per-PR event isolation.
Delivery is this change's normal PR.
Exit requires current-head PR checks and configured review.
Live scheduling verification requires the trusted base workflow to receive this change.

## Diagnosis

The breaking-label workflow already isolates each PR and event type.
It has one job and no dependency jobs.
However, it kept older runs active when a newer head emitted the same event.

On PR #389, the old-head synchronize run finished at 14:39:21 UTC.
The current-head run existed from 14:33:13, but its job appeared only at 14:39:22.
It then waited until 14:44:41 for a runner and completed at 14:44:46.
CI aggregation completed at 14:45:23.
Thus obsolete same-PR work caused 369 seconds of workflow waiting before a separate 319-second runner wait.
This was not a cross-PR group or a job dependency.

Evidence: [old-head run](https://github.com/TryUniCAD/Kit/actions/runs/46016911631) and [current-head run](https://github.com/TryUniCAD/Kit/actions/runs/46016960059).

## Behavior

A newer event cancels an older breaking-label run for the same PR and event type.
The event suffix remains: an edit cannot cancel the synchronize check required for the new head.
The current title, body and labels are still fetched before reconciliation.
Three bounded reconciliation attempts and fail-closed label validation remain unchanged.
Every required check name and CI allowlist entry remains.

Size, test, CI, dependency, documentation and direction labels already use per-PR groups with cancellation enabled.
They have no dependency jobs and need no scheduling change.
Diff breakdown intentionally preserves per-head immutable evidence with cancellation disabled.
That workflow is not changed or folded into another job.
All eight metadata workflow checks remain independently required.

## Verification and limits

Process scenarios execute the actual workflow JavaScript for adding, removing and retaining the label against current metadata.
They also retain per-event isolation and reject a reintroduced non-cancelling group.
These scenarios use the complete shared suite, planner, shards and completeness report.

Formatting, Python/JavaScript syntax, static steering and Git whitespace checks passed.
No local tests ran under repository policy.
PR CI and configured review remain pending.

The `pull_request_target` workflow executes from trusted base, so this PR cannot demonstrate its own new cancellation policy before merge.
After a separately authorized merge, compare two rapid synchronize events on one real PR.
The latest label job should no longer wait for the obsolete same-event run to finish.
Hosted runner delay can remain; no before-and-after live speedup is claimed here.
