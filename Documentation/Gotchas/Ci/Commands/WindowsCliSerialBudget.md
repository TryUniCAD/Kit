# Windows CLI qualification can dominate the queue

A successful heavy suite can appear to finish queue validation.
The separate Windows research CLI workflow also gates `CI Agg`.
Its serial command completed in 16m 27s on one candidate and consumed 18m 23s before cancellation on another.
The latter job was cancelled near its configured 20-minute limit, including setup and teardown.
The heavy suite passed, but the aggregate failed.

Keep the stable compatibility report while splitting its collected cases across Windows runners.
Require complete case outcomes and every shard before reporting success.
Use attempt-specific artifacts when collecting reports from parallel jobs.
Inspect associated workflow timings as well as `MergeQueue.yml` when identifying the queue critical path.
The separate macOS platform job also measured approximately 20 minutes and receives four shards in the same change.

See the [timing evidence and change](../../../Changes/Ci/Testing/WindowsResearchCliShards.md).
