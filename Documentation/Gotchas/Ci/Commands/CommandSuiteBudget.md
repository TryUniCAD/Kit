# Give CLI process coverage its own execution budget

An early workflow ran CLI processes and the native archive suite sequentially
under the archive job's 10-minute timeout. That assumed the CLI cases would
remain small. The earlier combined step already took 8 minutes 15 seconds;
expanded CLI coverage alone later took 269.30 seconds before archive execution.

The dedicated CLI and archive jobs were the earlier workaround.
The complete merge-queue suite now includes all their cases in its shared shards.
Preserve every case, the locked environment, schema verification, and the queue's existing job limits.
Use its runtime planner for expanded specialised coverage.

See the [shared compatibility suite](../../../Changes/Ci/SharedCompatibilitySuite.md)
and the [historical timing evidence](../../../Changes/Commands/CliProcessCi.md).
