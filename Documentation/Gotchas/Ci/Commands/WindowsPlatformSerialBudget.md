# Windows platform execution is separate from Windows CLI qualification

Sharding the Windows research CLI job does not shard the Windows platform process job.
They have separate rosters and independently gate the merge queue.

After Windows CLI sharding landed, PR #207's Windows platform job still took 20m 58s.
Its execution step consumed 20m 10s because the platform roster remained serial on one runner.
This was execution time rather than runner queueing or dependency installation.

Partition the Windows platform roster separately and retain the stable reporting gate.
Require complete outcomes and a native Windows pass across all reports.
Keep cases serial within each runner to preserve process isolation.

See the [baseline job](https://github.com/TryUniCAD/Kit/actions/runs/45036831854/job/137252637413)
and [Windows platform sharding](../../../Changes/Ci/Testing/WindowsPlatformShards.md).
