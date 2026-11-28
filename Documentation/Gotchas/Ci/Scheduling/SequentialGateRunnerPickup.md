# An empty gate still waits for a runner

Expected: a three-second compatibility assertion adds approximately three seconds after a report.
Actual: a dependent GitHub Actions job requires another hosted runner allocation before executing.

The [PR #375 candidate](https://github.com/TryUniCAD/Kit/actions/runs/46005349452) waited 135 seconds for its compatibility job and another 116 seconds for acceptance.
Their commands took three and four seconds respectively.
Both checked the same plan, shard and completeness-report results.

Keep the compatibility check, but run it in parallel with acceptance.
Acceptance must retain its direct completeness, platform and security dependencies.
CI aggregation must still require both native checks.
Do not replace native checks with fabricated successes or weaken result validation to reduce pickup delays.
See [parallel queue gates](../../../Changes/Ci/Scheduling/ParallelQueueGates.md).
