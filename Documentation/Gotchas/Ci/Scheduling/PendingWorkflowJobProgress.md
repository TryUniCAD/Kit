# A pending workflow can have active job progress

## Expectation

A workflow run status should identify whether its jobs have started.

## Observation

During [source audit 45288513439](https://github.com/TryUniCAD/Kit/actions/runs/45288513439), the workflow API continued to report `pending` with its original update timestamp.
At the same time, the paginated jobs API reported completed tests and scanners, an active test shard, and pending shards.
A separate job read confirmed that shard four had completed while the workflow still reported `pending`.
Fresh requests with distinct query values returned the same workflow status.
The cause and applicability to other workflow runs remain unverified.

## Workaround

Inspect the paginated job inventory and the exact commit checks while following this audit.
Use individual job metadata and logs to investigate a reported failure or stale job listing.
Require the final aggregate and acceptance results before declaring success.
Treat an empty jobs list as waiting evidence. Preserve active and pending runs.
