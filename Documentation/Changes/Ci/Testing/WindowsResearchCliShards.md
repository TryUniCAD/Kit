# Shard Windows CLI and macOS platform compatibility

## Task and behavior

Task `CI-WINDOWS-CLI-SHARDS` is owned by the implementation agent for this PR.
The scope covers Windows research CLI sharding, macOS platform sharding, and investigation of queue durations.
Dependencies are the locked Python 3.14 environment, candidate research checkout, and existing CI aggregator.
The delivery is [PR #230](https://github.com/TryUniCAD/Kit/pull/230).
The exit requires current-head PR checks and configured review. Native queue performance evidence remains deferred until authorized enrollment.

`Research CLI Windows compatibility` previously ran every selected case serially on one Windows runner.
The job now collects that same roster and assigns sorted node IDs across four Windows runners by round robin.
Parameterized cases can run on different runners. Each Windows shard retains the two pytest workers and file-level scheduling introduced by PR #229.
Each runner retains the separate candidate checkout, pinned history, sealed inputs, and locked dependencies.
No test paths, assertions, or timeout limits are removed.

Integration with main retains PR #229's worker scheduling and case-name output inside each Windows shard.
The stable report name remains in the same workflow for trusted-base aggregation.
It requires all four matrix jobs, identical collected rosters, successful sessions, and complete case outcomes.
The report rejects missing, repeated, failed, or unexpected outcomes.
Collection-time errors fail the shard before execution.
Artifacts contain each shard's collection, selected IDs, and pytest report log.
Artifact names include the run attempt to prevent upload collisions.
The reporter selects each shard's latest artifact within the same immutable workflow run.
A failed-job rerun can retain successful shards from earlier attempts of that run.
Reports from another workflow run are never downloaded.
Historical audits load the verifier from the workflow revision while native test shards retain the requested source revision.
See [the audit reporting gotcha](../../../Gotchas/Ci/Audits/ShardVerifierRevision.md).
The CI phase map registers every concrete shard. PR validation explicitly defers the skipped matrix template.

The macOS platform job also partitions its unchanged selected roster across four macOS runners.
It consumes the existing shared suite plan and publishes outcomes through the platform workflow.
Its stable report verifies complete coverage and requires an actual passing native macOS case across the combined reports.
Each shard runs serially to retain process isolation. The Windows platform process job retains its original single runner.

Each four-runner matrix repeats checkout and setup. Each adds three concurrent runner slots and one small Linux reporting job.
Runner contention can reduce the wall-time gain. This change does not modify organization limits or queue concurrency.

## Measured queue bottlenecks

Measurements are GitHub job timestamps on 2026-11-21, including setup and finalization.
They describe observed candidates, not a promised duration for this change.

| Job                                       | Observed job duration                 | Evidence and cause                                                                                                                                                                                                              | Next action                                                                                                                                            |
| ----------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Research CLI Windows compatibility        | 18m 03s successful; 20m 08s cancelled | [Successful workflow](https://github.com/TryUniCAD/Kit/actions/runs/44959401737), [cancelled job](https://github.com/TryUniCAD/Kit/actions/runs/44959082994/job/137013758668). Execution took 16m 27s and 18m 23s respectively. | This PR shards the existing roster. Measure the maximum shard duration on the candidate.                                                               |
| Test suite / Platform (macos-26)          | 19m 06s to 19m 55s                    | [Run 44959082941](https://github.com/TryUniCAD/Kit/actions/runs/44959082941), [run 44941240570](https://github.com/TryUniCAD/Kit/actions/runs/44941240570). Serial platform execution took 18m 22s to 19m 07s.                  | This PR partitions the selected roster with complete native-platform reporting.                                                                        |
| Test suite / Platform (windows-2025)      | 13m 04s in both runs                  | Same two queue runs. Serial execution took 12m 13s to 12m 19s.                                                                                                                                                                  | Shard this distinct platform process job after the CLI job.                                                                                            |
| Research CLI compatibility on Linux       | 9m 45s to 9m 53s                      | [Run 44959082994](https://github.com/TryUniCAD/Kit/actions/runs/44959082994), [run 44959401737](https://github.com/TryUniCAD/Kit/actions/runs/44959401737). Execution took 8m 49s to 8m 56s.                                    | Investigate retirement of duplicate Linux CLI execution through the documented trusted-base transition. The shared suite already includes these cases. |
| Slowest normal test shard                 | 7m 05s to 8m 15s                      | Runs 44959082941 and 44941240570. Test execution took 5m 53s to 6m 54s.                                                                                                                                                         | Compare case durations and balance before increasing the runner count.                                                                                 |
| Verify CI policy and pytest compatibility | 5m 42s to 7m 37s                      | Runs 44959082994 and 44959401737. Its native file exercise took 5m 04s to 6m 51s.                                                                                                                                               | Investigate duplicate execution relative to the complete suite, preserving every policy boundary.                                                      |
| CodeQL Python                             | 3m 01s to 3m 24s                      | Runs 44941240570 and 44959082941. Analysis took 2m 29s to 2m 48s.                                                                                                                                                               | Lower priority while serial platform jobs dominate.                                                                                                    |
| CodeQL Java; Grype                        | 2m 35s to 2m 37s; 1m 47s to 2m 13s    | Same successful queue workflows.                                                                                                                                                                                                | Preserve all scans. These jobs currently finish well before the critical path.                                                                         |

The shared planner took 54s to 72s; platform jobs start after it.
Measured platform start times add about 1m 03s to 1m 18s after workflow creation.
The resulting macOS path reached 20m 24s to 20m 58s after workflow creation.
These paths overlap: their durations must not be added together.
After Windows CLI and macOS sharding, the unchanged 13-minute Windows platform job is the largest measured remaining path.

`Merge queue acceptance` success does not establish overall queue success.
Run 44959082941 passed its heavy suite, while its associated Windows CLI job was cancelled and `CI Agg` failed.
The aggregate wait is a dependency wait, not evidence that its own computation is the bottleneck.
Linux compatibility, normal shard scheduling, security scanners, and organization settings remain unchanged.

## Validation record

The author inspected two completed heavy queue runs and associated workflow job and step timestamps.
The author also inspected the successful 18-minute Windows CLI run and the cancelled 20-minute run.
The existing aggregator process coverage now checks every concrete Windows CLI and macOS shard under failure, skip, cancellation, timeout, neutral, and success outcomes.
New report-process compatibility cases reject missing, duplicated, failed, unexpected, and mismatched outcomes, failed sessions, missing native passes, and incorrect artifact precedence across rerun attempts.
These cases use the complete suite's existing planner, runners, and report.
No local tests ran under the repository execution policy.
PR checks and configured review run on [PR #230](https://github.com/TryUniCAD/Kit/pull/230).
Formatting and shell syntax checks passed before publication. Process-compatibility execution remains deferred to the shared queue suite.
Queue acceptance and measured improvement require the synthetic candidate after administrator-authorized enrollment.
No native CAD decoding, conversion, or vendor acceptance is claimed.
