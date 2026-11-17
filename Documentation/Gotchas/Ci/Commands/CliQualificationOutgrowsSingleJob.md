# CLI qualification coverage can exceed a single job budget

The earlier 766-case CLI run finished in 380.95 seconds on one runner. A later
775-case run progressed at roughly 72 cases per minute and reached 83 percent
before the unchanged ten-minute job timeout cancelled it. Passing archive or
static checks does not make that incomplete CLI execution successful.

The dedicated core and qualification groups were the earlier workaround.
The complete merge-queue suite now schedules these cases across its normal shards.
Keep every case in the shared suite and preserve the locked environment and schema provenance check.
The shared planner balances their execution with all other collected tests.

See the [shared compatibility suite](../../../Changes/Ci/SharedCompatibilitySuite.md)
and the [historical group workflow](../../../Changes/Commands/CliProcessGroups.md).
