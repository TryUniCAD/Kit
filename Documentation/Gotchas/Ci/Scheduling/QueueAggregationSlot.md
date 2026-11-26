# Per-candidate queue aggregation needs a paced, rate-limit-tolerant poller

## Expectation

Giving each merge-queue candidate its own `CI Agg` concurrency slot only costs one more runner per candidate; the aggregation script can poll as it does on pull requests.

## Actual behavior

The pull-request poller lists the revision's workflow runs and check runs (two to three REST requests) every 30 seconds: roughly 240–360 requests an hour per poller.
`GITHUB_TOKEN` allows [1,000 REST requests per hour per repository](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api) outside Enterprise Cloud, shared with every other workflow job in the repository.
Three to four concurrent candidates polling that way would exhaust it, and the live queue builds up to 25.
Before [queue aggregation polling](../../../Changes/Ci/Scheduling/QueueAggregationPolling.md), a rate-limit response (HTTP 403) was exempt from the aggregator's retries, so the candidate's `CI Agg` failed: one of 184 failed queue `CI Agg` runs from 20–26 November 2026 failed this way with a single poller (run 44800979466).

The opposite choice, one shared queue slot, is not safe either: it times out healthy candidates.
An earlier version of this page recommended keeping the shared slot because `CI Agg` finished a median 0.4 minutes after the last job of each successful candidate.
That sample left out candidates the slot ejected; see [the queue aggregation timeout gotcha](QueueAggregationTimeout.md).

## Workaround

Pace queue polling from the live rate limit, use conditional requests so unchanged polls are free, and treat rate-limit responses as waits before giving each candidate its own slot.
[Queue aggregation polling](../../../Changes/Ci/Scheduling/QueueAggregationPolling.md) does this and must reach `main` first, because the merge-group `CI Agg` loads its script from the candidate's base commit.
Each per-candidate aggregator still holds a hosted runner while it waits.
