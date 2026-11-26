# Per-candidate queue aggregation

## Behavior

Each merge-group candidate's `CI Agg` job now has its own concurrency group, `Kit-aggregation-queue-<merge_group.head_sha>`.
Before, every candidate shared one `Kit-aggregation-queue` group with `queue: max`, so aggregators ran one at a time in the order they were queued.
Each running aggregator held that slot until its own candidate finished.
Later candidates' aggregators could wait past the live 60-minute queue response timeout even when every other check had passed, and GitHub then removed the candidate.

A candidate's `CI Agg` now starts with the candidate and reports within one poll interval of its last check: about 30 seconds while most polls return `304`, up to about three minutes when every poll is charged.
Re-runs of the same candidate still share its group and run one at a time.
Pull-request aggregation keeps its per-PR group.
The aggregated checks, failure rules and 80-minute aggregation deadline are unchanged.

## Ordering

This change depends on [queue aggregation polling](QueueAggregationPolling.md), which must be on `main` first.
The merge-group `CI Agg` loads `CiReports.cjs` from the candidate's base commit, while this concurrency group comes from the candidate's own workflow file.
Without the paced polling in the base, concurrent aggregators would each poll every 30 seconds, exceed the repository's `GITHUB_TOKEN` limit of 1,000 REST requests per hour, and fail on rate-limit responses.

## Cost

Each building candidate holds one more hosted Linux runner while its aggregator waits, counted against the Team plan's 60 concurrent jobs. The cooperating lane budget is 28 jobs on `main`, 35 with the separate pull-request lanes and 39 with the Windows CLI lanes. At the ruleset's 25-build limit, 25 aggregators plus 39 lane jobs would exceed 60, and GitHub would queue the excess jobs until runners free up; they wait, they do not fail. Up to eight candidates were observed building at once on 26 November 2026.

API use stays within the `GITHUB_TOKEN` limit at 25 candidates because of [queue aggregation polling](QueueAggregationPolling.md). Each later poll is one conditional request, so a `304` does not count against the limit. Each aggregator spends at most 1/25 of the budget above a reserve of 500, spread over the time to reset, so all 25 together never take the remaining budget below 500. With a full budget and an hour to reset, 25 aggregators poll every 180 seconds, 500 requests in total. A rate-limit response delays `CI Agg` instead of failing it. The rate budget section of that entry has the arithmetic, including other jobs' use.

See [the queue aggregation timeout gotcha](../../../Gotchas/Ci/Scheduling/QueueAggregationTimeout.md).

## Verification

The queue and pull-request aggregation process cases in `tests/Policy` pass locally, and Zizmor reports no findings.
The failure this fixes is recorded in the gotcha (#354's candidate `57b7526`, removed at 14:30:41 UTC on 26 November 2026).
Queue timing needs candidates after both changes reach `main`.
