# Abandoned aggregation runs block the queue

`CI Agg` in `PullRequest.yml` serializes every merge-group run on one concurrency group with `queue: max` and no cancellation.
A run left behind by a removed candidate keeps that group occupied.
Every later candidate's `CI Agg` then stays pending until the queue's 60-minute check timeout removes it.

On 26 November 2026, PR 355 timed out twice this way.
Its `CI Agg` job stayed pending from 14:30 to 15:31 UTC behind eleven runs whose synthetic branches no longer existed.
Cancelling only those runs let the current candidate's aggregation start immediately.

The trusted cleanup previously accepted only `MergeQueue.yml` and `WorkflowQuality.yml`, so it never released these runs.
`PullRequest.yml` is now in the cleanup allowlist, under the same identity and queue-evidence checks.
