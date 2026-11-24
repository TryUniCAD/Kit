# Shared CI runner budget

## Behavior

Heavy repository jobs share eight Linux lanes, five Windows lanes, and five macOS lanes through GitHub job concurrency groups.
Two of the twenty hosted-job slots remain outside those worker lanes for planning, aggregation, and short control work.
The shared groups cover native-file compatibility, installed Windows CLI compatibility, Python quality, and workflow validation.
They bound cooperating heavy jobs across candidates and manual runs, rather than only within one matrix.
Organization-wide jobs and GitHub-managed Code Quality scans can still compete for the same hosted allowance.
Native queue aggregation uses one waiting lane so speculative candidates do not each hold a polling runner.
PR aggregation retains independent per-PR concurrency, so a blocked PR cannot hold other PR reports behind it.
Short control jobs are not a separately reserved GitHub runner group and can still queue briefly.

Manual full-suite audits use one workflow concurrency group with `queue: max`.
GitHub retains up to one hundred pending requests instead of replacing the previous pending audit.
An audit waits until the native merge queue is empty and its unfinished merge-group workflows have ended.
Admission errors fail closed; a continuously busy queue times out admission after one hour.
No audit is reported as accepted when admission fails.
All heavy audit jobs depend on successful admission and collection.

Audit Windows and macOS shards execute one at a time in the fifth native lane.
The first four native lanes remain available to merge candidates arriving during an audit.
Audits retain fresh test execution, their requested source SHA, feature-session input, and every reporting gate.
All heavy Linux audit jobs share only lanes six and seven, including scanners and at most two concurrent test shards.
The first six Linux lanes remain available to later merge candidates.
This gives merge acceptance priority; complete manual audits can take longer than an unconstrained isolated audit.

## More sharding within the budget

After the trusted base includes `.github/CiResources.json` and the updated allowlist, expansion also requires live queue settings of one build, one minimum entry, and zero batching wait.
Unavailable rules disable expansion.
An eligible candidate uses five native shards when no audit is active or pending.
An active or pending audit retains four candidate shards, with the audit occupying the fifth lane.
Linux uses a one-thousand-test cap and the existing twelve-hundred-test-second target, with eight runtime-requested shards.
Additional shards required by the test-count cap reuse those same eight lanes.
All platform selections retain duration weighting and exact-once roster verification.
Every security scan waits for collection to pass before starting, so a rejected collection does not fan out expensive scanners.
Security checks remain required for acceptance.

The first rollout candidate retains four native shards and the previous count cap because its trusted base cannot yet recognize fifth-shard checks.
Manual audits of older source revisions keep the legacy count planner and modulo platform selection.
The admission harness comes from the workflow revision, not the older audited source.
Dispatch future audits from the current `main` harness with `audit_sha` selecting the source revision.
Older workflow definitions and running audits cannot be retroactively placed in the new groups.

The analyzer is pinned to actionlint concurrency-support revision `644076a59742c2d1540ebd4686eab3c308f0e562` from upstream PR 654.
It is built with Go 1.26.0 and read-only module resolution, then cached by source and compiler identity.
No lint rule is suppressed to accept the new concurrency key.

## Operation and verification

Task: future CI runner scheduling; owner: Codex; delivery [PR #276](https://github.com/TryUniCAD/Kit/pull/276).
Scope: resource admission, bounded fanout, and fail-fast collection; dependency: default-branch rollout.
Exit: current-head PR gates and configured approval, followed by separately authorized native acceptance and measured timing.

The complete suite exercises scheduler entry processes with simulated GitHub metadata and executes real pytest selections through four- and five-shard native reporting.
Remote execution remains pending.
Source and process coverage do not establish GitHub scheduling fairness or an end-to-end speedup.
Measure setup, runner wait, execution, and final aggregation after rollout.
The [workflow progress observation](../../Gotchas/Ci/Scheduling/PendingWorkflowJobProgress.md) records an audit whose workflow status stayed pending while its job inventory advanced.
Follow the job inventory and final gates when checking that run.

The live queue remains separately configured.
The shared concurrency queues retain at most one hundred pending jobs per lane; they are not unlimited admission queues.
An administrator must apply one candidate build, one minimum merge entry, and zero batching wait to the existing queue rule while preserving every other protection.
The PR does not mutate repository settings, cancel other work, or change acceptance requirements.
See [manual audit contention](../../Gotchas/Ci/Scheduling/ManualAuditRunnerContention.md) and [concurrency validator support](../../Gotchas/Ci/Scheduling/ConcurrencyQueueValidator.md).

See the [native report count gotcha](../../Gotchas/Ci/Shards/NativeReportShardCount.md) for five-shard reporting compatibility.

## Queue acceptance fixture repair

Two candidate attempts exposed a fixture parser that omitted every dynamic native shard check.
The repair recognizes the native fallback expression, emits four or five explicit reports, and rejects unknown matrix definitions or absent target checks immediately.
Queue aggregation process cases now cover both fifth native checks across all existing verdicts and workflow outcomes.
Required native checks, complete workflow outcomes, security gates, and twenty‑second subprocess deadlines remain unchanged.
Fresh combined‑revision remote acceptance is pending.
See the [dynamic matrix fixture gotcha](../../Gotchas/Ci/Scheduling/DynamicMatrixAggregationFixtures.md).
