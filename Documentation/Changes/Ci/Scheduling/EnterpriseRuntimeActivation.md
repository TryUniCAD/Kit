# Enterprise runtime planning activation

## Ownership

Task CI runtime activation; owner Hoplite; scope is Linux shard sizing under the trusted Enterprise capacity marker.
Dependencies are the existing runtime planner, duration history and complete-suite reports.
The delivery is this change's normal PR.
Exit requires current-head PR checks and configured review.
Candidate timing and acceptance require separate administrator-authorized queue enrollment.

## Behavior

Version 5 of the trusted resource marker enables Linux runtime planning independently of live queue batching settings.
It selects 1,200 estimated test seconds per shard and a 1,000-test count cap.
The workflow retains its 256-shard runtime ceiling and four pytest workers per Linux shard.
Missing duration history retains count-based sizing.
Older resource markers retain their existing live-settings activation conditions.
Malformed markers and marker API failures still reject selection.

Native platform shard counts retain their existing queue-setting and audit checks.
This change does not modify any live ruleset, admission setting, check name, roster, assertion or completeness report.
Accepted-ancestor dependency checks remain the only basis for reusing test results.

## Diagnosis

Enterprise capacity landed in PR #363, but Linux planning still depended on the older native-platform expansion condition.
The live queue requires two entries with a ten-minute batching wait.
That condition selected runtime target zero, even with the trusted Enterprise marker.
The seven Linux shards on the successful [PR #375 candidate](https://github.com/TryUniCAD/Kit/actions/runs/46005349452) therefore used count-based sizing.
Its final aggregate finished 17 minutes 38 seconds after the queue event.

The owner-preserved ruleset remains unchanged: 25 candidate builds, minimum two entries, ten-minute batching wait and 60-minute timeout.
See [the activation gotcha](../../../Gotchas/Ci/Scheduling/EnterpriseRuntimeBatching.md).

## Verification

The existing scheduling process scenarios cover Enterprise selection with live batching, invalid limits and unavailable rule reads.
They also retain legacy-marker fallback, malformed-marker rejection and audit-dependent native sizing.
The existing planner process coverage checks runtime allocation through actual pytest execution and exact-once result reporting.
These scenarios remain in the shared complete suite and merge-queue execution path.

Black, Prettier, JavaScript syntax checks and Git whitespace checks passed for the changed files.
No local tests ran under repository policy.
Remote PR checks, configured review and post-change candidate timing remain pending.
No measured speedup or under-ten-minute result is claimed before candidate execution.
