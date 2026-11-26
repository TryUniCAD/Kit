# One queue aggregation slot times out healthy candidates

## Expectation

A single `Kit-aggregation-queue` concurrency slot for merge-group `CI Agg` only delays aggregation: candidates finish in roughly the order they were queued, so each aggregator gets the slot as its candidate completes.

## Actual behavior

The slot starts `CI Agg` jobs strictly in the order they were queued.
Each running aggregator then holds the slot until its own candidate finishes, often 10–40 minutes.
Aggregators for superseded candidates also wait their turn before failing in about 25 seconds.

On 26 November 2026, five candidates were created at 13:29 UTC (PRs #300, #298, #288, #354 and #353).
None of their `CI Agg` jobs had started an hour later.
Candidate `57b7526` for #354 (Pull Request run 45829667989) passed every other check, including `Merge queue acceptance` at 14:25.
Its `CI Agg` had waited since 13:29:42 behind earlier aggregators.
GitHub removed #354 at 14:30:41, 61 minutes after it was enqueued, matching the live 60-minute queue response timeout.
Every later candidate was then rebuilt.

Counting only successful candidates hides this: for those, `CI Agg` finished a median 0.4 minutes after their other jobs.
Candidates that time out never succeed, so they drop out of that sample.

## Workaround

Give each candidate its own aggregation slot.
Each aggregator must stay within the repository's [1,000 REST requests per hour](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api) `GITHUB_TOKEN` limit even with 25 candidates building, so pace queue polling by the live remaining budget first.
See [queue aggregation polling](../../../Changes/Ci/Scheduling/QueueAggregationPolling.md).
