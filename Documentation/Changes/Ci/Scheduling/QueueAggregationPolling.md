# Queue aggregation polling

## Behavior

On merge-group candidates, `CI Agg` now polls the candidate's checks less often.
After a poll finds pending checks, it waits until ten minutes after the candidate's merge commit was created (`merge_group.head_commit.timestamp`), and at least two minutes between polls after that.
Pull-request aggregation keeps its 30-second interval.
The first poll still runs immediately, so a candidate whose checks have already finished or failed is reported without waiting.

Each poll lists the candidate's workflow runs and check runs, two to three REST requests.
At 30-second polling that is roughly 240–360 requests an hour per aggregator.
After this change, an aggregator makes about three requests in its first ten minutes and then about 90 an hour.

This prepares for giving each candidate its own `CI Agg` concurrency slot, a separate change that must land after this one.
`GITHUB_TOKEN` allows 1,000 REST requests per hour per repository, shared with every other job.
At the old rate, three or four aggregators running at once would exhaust that limit; at the new rate, about ten can poll for a whole hour before reaching it.
The merge-group `CI Agg` loads this script from the candidate's base commit, so the new rate applies only once this change is on `main`.

## Limits

A candidate's `CI Agg` can report up to two minutes after its last check finishes.
With the current single queue aggregation slot, an aggregator that starts within ten minutes of its candidate's creation now holds the slot idle until then.
Candidates rarely finish their checks within ten minutes, so this mainly adds polling delay until the per-candidate slot lands.
The 80-minute aggregation deadline, the failure rules and the set of aggregated checks are unchanged.

See [the queue aggregation timeout gotcha](../../../Gotchas/Ci/Scheduling/QueueAggregationTimeout.md).

## Verification

The queue and pull-request aggregation process cases in `tests/Policy` pass locally (629 cases).
The merge queue evidence that motivated this change is in the gotcha.
Rate and wall-clock effects need queue candidates after this change reaches `main`.
