# Queue runtime scheduling

## Behavior

The desired queue builds one candidate at a time.
It retains one entry as the merge minimum and zero minutes of batching wait.
These values reserve capacity for the candidate's four native platform shards.
The manifest does not update live repository settings.

Platform shards use their own platform's recorded case durations.
The planner downloads Windows and macOS histories into the shared plan artifact.
Every shard therefore uses the same immutable history for its candidate.
Missing history uses deterministic fallback weights.
API and download failures also use fallback weights without consuming incomplete downloads.
Malformed history fails planning rather than changing coverage.

The platform reports publish durations only after exact-once coverage and native passes succeed.
Duration inputs come from same-repository merge-group runs of `MergeQueue.yml`.
Durations affect scheduling only; they never authorize test-result reuse.
The existing accepted-ancestor dependency checks still control reuse.

Linux planning retains the 1,200-test cap.
It also requests enough shards for 1,200 estimated CPU seconds per shard, up to eight runtime-requested shards.
The test-count cap can require additional shards beyond that runtime budget.
The four-worker execution path retains slow/fast pairing.
This estimate is not an elapsed-time acceptance target.
Unknown cases use the existing median-duration estimate.
Without measured history, the existing count-based sizing remains active.

## Configuration and operation

`tools.TestShards.PlanShards` accepts `--target-seconds` and `--runtime-shards`.
The defaults disable runtime sizing and limit runtime-requested shards to eight.
The runtime target must be finite and nonnegative; the shard budget must be positive.
The queue supplies `--target-seconds 1200 --runtime-shards 8` only after verifying the live scheduling settings.
Until build concurrency, merge minimum, and batching wait are `1`, `1`, and `0`, runtime expansion remains disabled.
Manual audits retain count-based sizing and modulo platform selection.
They do not invoke scheduling additions absent from older source revisions.
Native platforms retain four serial shards each.
Duration uploads replace earlier successful reports when the same report job is rerun.
No security checks, assertions, or acceptance contexts are removed.

Before changing live settings, an authorized administrator must inspect the existing `Protect` ruleset.
Update only its queue build concurrency, merge minimum, and minimum-entry wait.
Use `1`, `1`, and `0` respectively.
Preserve every other protection and required check.
Read the branch rules back to confirm the accepted values.
See [merge queue operations](../../../MergeQueue.md) and [configuration drift](../../Gotchas/Ci/Scheduling/QueueSettingsDrift.md).

## Evidence and limits

Task: queue runtime scheduling, owned by Codex in [PR #264](https://github.com/TryUniCAD/Kit/pull/264).
Scope: queue scheduling and its existing complete-suite execution path.
Dependencies: separate administrator activation of live queue settings.
Exit conditions: current-head PR gates and configured review, followed by authorized candidate acceptance and measured latency evidence.

The repair records [Windows roster newlines](../../Gotchas/Ci/Windows/SelectedRosterNewlines.md),
[historical scheduler compatibility](../../Gotchas/Ci/Audits/SchedulerSourceRevisions.md), and
[duration artifact reruns](../../Gotchas/Ci/Scheduling/DurationArtifactReruns.md).
Process fixtures also follow the [sorted platform roster contract](../../Gotchas/Ci/Scheduling/SortedPlatformRosters.md).

The investigation inspected [candidate 45065850751](https://github.com/TryUniCAD/Kit/actions/runs/45065850751).
Its final macOS shard started 10 minutes 17 seconds after planning completed.
macOS test execution ranged from 3 minutes 21 seconds to 7 minutes 33 seconds.
Windows execution ranged from 4 minutes 58 seconds to 7 minutes 32 seconds.

Process-boundary coverage collects and executes a real pytest sample through both scheduling paths and their reporting gates.
The complete queue suite owns these tests; no separate runner or workflow is added.
Execution evidence remains pending until remote CI runs the changed tests.
No before-and-after queue speedup is established by source inspection.
Live queue-setting activation remains separate from this code change.
After activation, compare candidate latency and merged entries per hour across comparable workloads.
