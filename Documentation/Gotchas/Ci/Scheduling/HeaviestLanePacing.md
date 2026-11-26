# The heaviest lane paces every queue candidate

## Expectation

Removing the longest job, or moving it off a lane, shortens merge-queue candidates by about that job's duration.

## Actual behavior

Lanes use `queue: max`, and GitHub starts waiting jobs in the order they began waiting, not in candidate order.
When several candidates build at once, every candidate's jobs queue together on each lane.
A candidate therefore finishes only after the lane has worked through roughly every earlier-waiting candidate's share.
Candidate wall time grows by about the heaviest lane's per-candidate load for each candidate building alongside it.

After PR #347 removed the 11-minute research CLI job from `Kit-linux-2`, the next four candidates took 23.7, 32.5, 38.8 and 44.5 minutes.
They finished about 6 minutes apart, and each one's last jobs were its Windows platform shards.
`Kit-windows-shard-1` to `shard-4` each carry a Windows research CLI shard and a Windows platform shard, about 8.6 minutes per candidate.
That makes them the heaviest lanes.
The `Kit-test-linux-*` lanes follow at about 6 minutes per candidate: each candidate's seven shards took their turn on lanes 0–6 behind the candidates queued earlier, so PR #347's shards waited 12–15 minutes behind the #349 and #297 shards.

## Workaround

Sum each lane's job durations per candidate and compare the maximum across every lane family: `Kit-linux-*`, `Kit-test-linux-*`, `Kit-windows-*` and `Kit-macos-*`.
Shortening anything other than the heaviest lane does not change candidate pacing.
Measure with the jobs API (`created_at`, `started_at`, `completed_at`) for every run of a candidate's `head_sha`.
See [balanced scanner lanes](../../../Changes/Ci/Scheduling/BalancedScannerLanes.md).
