# One queue aggregation slot keeps CI Agg inside the token rate limit

## Expectation

The single `Kit-aggregation-queue` concurrency group for merge-group `CI Agg` serializes candidates end to end, so scoping it per candidate (per `merge_group.head_sha`) should shorten the queue.

## Actual behavior

The slot rarely delays a successful candidate.
Lanes serve candidates first in, first out, so candidates usually finish in the order their `CI Agg` jobs queue.
In 29 successful candidates from 23–26 November 2026, `CI Agg` finished a median 0.4 minutes after the candidate's last other job.
In 3 of them it started 4.6–6.6 minutes after the candidate's other jobs had finished, because an earlier candidate was still running (#275, #284 and #289; #289 waited behind a re-run of #297).

Scoping the group per candidate would start one poller per building candidate.
Each poll lists the revision's workflow runs and check runs (two to three REST requests) every 30 seconds, roughly 240–360 requests an hour per poller.
`GITHUB_TOKEN` allows [1,000 REST requests per hour per repository](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api) outside Enterprise Cloud, shared with every other workflow job in the repository.
Three to four concurrent candidates would exhaust it, and the live queue builds up to 25.
A rate-limit response (HTTP 403) is exempt from the aggregator's retries, so the candidate's `CI Agg` would fail.
Per-candidate pollers would also each hold a hosted runner for the candidate's whole duration, which the shared runner budget avoids.

## Workaround

Keep the single queue aggregation slot.
Shorten candidates by relieving the heaviest worker lanes; the aggregation slot then follows the order in which candidates finish.
Revisit per-candidate aggregation only with a lower request rate per poll or a larger token budget.
See [balanced scanner lanes](../../../Changes/Ci/Scheduling/BalancedScannerLanes.md).
