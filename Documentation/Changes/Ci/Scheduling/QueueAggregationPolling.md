# Queue aggregation polling

## Behavior

On merge-group candidates, `CI Agg` now polls in a way that stays within the repository's GitHub API budget even with 25 candidates building at once.

- **First read.** `CI Agg` reads all of the candidate's workflow runs and check runs once at start, as before. A candidate whose checks have already finished or failed is reported at once.
- **Cheap polls.** Each later poll is one request for the candidate's workflow runs (`GET /repos/{owner}/{repo}/actions/runs?head_sha=`), sent with the previous `ETag` in `If-None-Match`. A `304 Not Modified` reply does not count against the primary rate limit. The full check read runs again only when every registered workflow run has completed or one has completed without success. A failed workflow therefore still fails `CI Agg` as soon as that workflow completes.
- **Paced polls.** Before each wait, `CI Agg` reads `GET /rate_limit`, which does not count against the limit. It then waits the longest of:
  - 30 seconds;
  - until eight minutes after the candidate's merge commit was created (`merge_group.head_commit.timestamp`); the fastest successful candidate measured from 23 to 26 November 2026 finished its last job after 10.6 minutes;
  - its fair share of the remaining budget, counting only charged polls: `seconds until reset × 25 / (remaining − 500) × charged polls / polls`.

  A `304` reply is free, so while most polls return `304` the 30-second floor applies. If every poll is charged, the interval grows to the full fair share.

  When 500 or fewer requests remain, it waits until the limit resets.
- **Rate limits are waits.** A `403` or `429` rate-limit response, primary or secondary, makes `CI Agg` wait for `Retry-After` or `x-ratelimit-reset` and try again, never fail. This applies to pull-request aggregation as well. Other errors, including a `403` that is not a rate limit, still fail.

Pull-request aggregation keeps its 30-second interval. The 80-minute aggregation deadline, the failure rules and the set of aggregated checks are unchanged.

This prepares for giving each candidate its own `CI Agg` concurrency slot, a separate change that must land after this one. The merge-group `CI Agg` loads this script from the candidate's base commit, so the pacing applies only once this change is on `main`.

## Rate budget

`GITHUB_TOKEN` allows [1,000 REST requests per hour per repository](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api) outside Enterprise Cloud, shared by every workflow job. The pacing reads the live limit, so a larger limit simply allows faster polling.

- **One aggregator.** Its first and final reads cost two to three requests each. Each poll in between costs one request, or none when GitHub answers `304`.
- **25 aggregators.** The ruleset builds at most 25 candidates at once. Each aggregator's charged polls are paced to at most 1/25 of the budget above 500, spread over the time to reset. Together they therefore stay above 500 remaining.
  - With a full budget of 1,000 and an hour to reset, and every poll charged, each polls every 180 seconds: 20 requests an hour each, 500 in total.
  - With half the polls answered `304`, the interval halves to 90 seconds at the same charged rate. With mostly `304` replies, it reaches the 30-second floor.
  - As other jobs spend, the intervals lengthen.
- **Other jobs.** Their spend grows with candidate throughput, not with the number of candidates building. The lanes limit throughput to about ten candidates an hour. Before this change, one aggregator polling every 30 seconds (240–360 requests an hour) ran alongside them. One of 184 failed queue `CI Agg` runs from 20–26 November failed on `API rate limit exceeded for installation` (run 44800979466, PR #202's candidate on 20 November). Their peak use is therefore about 650–750 an hour.
  - Take other jobs at 700 an hour, evenly spread. The aggregators then spend about 140 requests in that hour and stop polling about half an hour before the reset. The total is about 840, under the limit.
  - Because they wait on rate limits instead of failing, a busy hour delays `CI Agg` rather than ejecting the candidate.

## Limits

`CI Agg` reports within one poll interval after a candidate's workflows complete: 30 seconds while `304` replies dominate, up to about 3 minutes when every poll is charged. In a fully busy hour the interval can grow further, or to the time until reset once 500 or fewer requests remain. The live queue response timeout is 60 minutes, so a candidate that is still waiting can still time out. The fair share assumes at most 25 concurrent aggregators, matching the ruleset's build limit.

Until per-candidate slots land, all queue aggregators still share one concurrency slot, and a held slot now idles longer between polls.

See [the queue aggregation timeout gotcha](../../../Gotchas/Ci/Scheduling/QueueAggregationTimeout.md).

## Verification

`tests/Policy/QueueAggregationTests.py` runs `.github/scripts/CiReports.cjs` in a Node process. Fake GitHub responses and a fake clock drive one candidate through these cases:
- the eight-minute idle, then the fair-share interval at full budget (156 s after a charged poll), halved to 75 s after a free `304`;
- an unchanged `304` poll;
- a primary `403` rate limit, waiting 601 s until the reset, then success;
- a secondary `429` rate limit, waiting 60 s for `Retry-After`;
- a non-rate-limit `403`, which fails;
- fair-share pacing at 600 remaining (900 s);
- waiting until the reset at 450 remaining;
- a failed workflow, which fails `CI Agg`.

All 636 `tests/Policy` cases pass locally. Rate and wall-clock effects need queue candidates after this change reaches `main`. The aggregator logs the remaining budget at every poll as evidence.
