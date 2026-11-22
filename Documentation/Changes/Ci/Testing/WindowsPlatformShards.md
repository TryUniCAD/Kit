# Shard Windows platform process checks

## Task and behavior

Task `CI-WINDOWS-PLATFORM-SHARDS` is owned by the implementation agent for this PR.
Its scope is the Windows platform process job in `MergeQueue.yml`.
Dependencies are the shared collected roster, Python 3.14 lockfile, existing artifact verifier, and CI aggregator.
The delivery is a separate PR from the earlier Windows CLI and macOS sharding change.
The exit condition requires current-head PR checks and configured review.
Queue acceptance and measured timing require a candidate after administrator-authorized enrollment.

`Test suite / Platform (windows-2025)` previously executed its complete selected roster on one Windows runner.
Four Windows runners now partition the same sorted roster by round robin.
Each runner executes its assigned cases serially to preserve process isolation.
The selection patterns, native Windows requirement, lockfile, runner image, assertions, and execution timeout are unchanged.

The stable Windows platform job becomes a Linux reporting job.
It requires every Windows shard to succeed.
It also verifies identical collected rosters, one outcome per selected case, complete combined coverage, successful sessions, and an actual native Windows pass.
Failed, skipped, cancelled, or missing shards cannot satisfy acceptance.
The existing verifier selects each shard's latest artifact within the same workflow run and attempt history.
It rejects a failed newer attempt instead of accepting an older successful artifact.
Historical source audits load the verifier from the workflow revision while tests use the requested source revision.

All four concrete shard names are registered in the CI allowlist.
The skipped PR matrix template is explicitly deferred.
The queue acceptance job depends directly on both the Windows shards and their stable report.
Existing reporting-process and aggregator-process compatibility coverage includes the new Windows names and artifact prefix.
These checks remain in the complete suite and its shared queue planner.

The matrix adds three concurrent Windows runner slots and one small Linux reporting job.
Runner availability and repeated checkout costs can reduce the wall-time improvement.
This change does not alter queue concurrency or organization limits.

## Baseline and timing limits

[PR #207's queue run](https://github.com/TryUniCAD/Kit/actions/runs/45036831854)
used candidate `ac003be16678fcf47989dfdda6c2d08d1dc8777e` on 2026-11-22.
Its [Windows platform job](https://github.com/TryUniCAD/Kit/actions/runs/45036831854/job/137252637413)
took 20m 58s overall and 20m 10s in its execution step.
The report contained 315 call outcomes: 305 passed and 10 skipped.
Windows rearm cases consumed approximately 148 seconds; calibration cases consumed approximately 100 seconds.

A static partition of that recorded roster gives the following observed call-time sums.
This calculation does not execute the new workflow or establish its candidate duration.
It excludes setup, scheduling, teardown, and any change in case duration.

| Shard | Cases | Recorded call-time sum |
| ----- | ----- | ---------------------- |
| 1     | 79    | 251.5 seconds          |
| 2     | 79    | 397.2 seconds          |
| 3     | 79    | 255.4 seconds          |
| 4     | 78    | 294.8 seconds          |

The largest recorded partition is approximately 6m 37s of call time.
Actual improvement remains unmeasured until the native Windows shards execute.

## Verification

The author inspected the baseline job steps and its published report artifact.
The baseline calculation above uses those recorded outcomes without running tests locally.
Formatting and syntax checks run before publication.
Process compatibility checks run through remote CI and the existing queue suite.
No test coverage, security gate, native-platform assertion, or timeout is removed.
This change does not claim CAD conversion or vendor application acceptance.
