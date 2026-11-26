# Per-candidate queue aggregation

## Behavior

Each merge-group candidate's `CI Agg` job now has its own concurrency group, `Kit-aggregation-queue-<merge_group.head_sha>`.
Before, every candidate shared one `Kit-aggregation-queue` group with `queue: max`, so aggregators ran one at a time in the order they were queued.
Each running aggregator held that slot until its own candidate finished.
Later candidates' aggregators could wait past the live 60-minute queue response timeout even when every other check had passed, and GitHub then removed the candidate.

A candidate's `CI Agg` now starts with the candidate and reports within about two minutes of its last check.
Re-runs of the same candidate still share its group and run one at a time.
Pull-request aggregation keeps its per-PR group.
The aggregated checks, failure rules and 80-minute aggregation deadline are unchanged.

## Ordering

This change depends on [queue aggregation polling](QueueAggregationPolling.md), which must be on `main` first.
The merge-group `CI Agg` loads `CiReports.cjs` from the candidate's base commit, while this concurrency group comes from the candidate's own workflow file.
Without the slower polling in the base, several concurrent aggregators would poll every 30 seconds and could exceed the repository's `GITHUB_TOKEN` limit of 1,000 REST requests per hour.

## Cost

Each building candidate holds one more hosted Linux runner while its aggregator waits; GitHub counts that against the Team plan's 60 concurrent jobs.
With the slower polling, one aggregator makes about 90 REST requests an hour after its first ten idle minutes.
About ten candidates can aggregate at once for a whole hour within the 1,000-request limit.
The live queue setting allows 25 concurrent builds, so a full queue could still approach that limit; most aggregators finish well within the hour.

See [the queue aggregation timeout gotcha](../../../Gotchas/Ci/Scheduling/QueueAggregationTimeout.md).

## Verification

The queue and pull-request aggregation process cases in `tests/Policy` pass locally, and Zizmor reports no findings.
The failure this fixes is recorded in the gotcha (#354's candidate `57b7526`, removed at 14:30:41 UTC on 26 November 2026).
Queue timing needs candidates after both changes reach `main`.
