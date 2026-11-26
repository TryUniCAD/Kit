# Per-candidate queue aggregation

## Behavior

PR #359 proposed replacing the shared `Kit-aggregation-queue` concurrency group
with a group keyed by each merge-group candidate's head SHA. The shared group
serialized aggregators and could time out otherwise healthy candidates.

[Enterprise hosted concurrency](EnterpriseLaneSets.md), delivered by PR #363,
removed the aggregation job's concurrency group entirely before #359 landed.
This conflict resolution preserves that implementation: each candidate's
aggregator can run independently, subject to GitHub's hosted capacity.
Workflow-level isolation remains enabled. No job-level lock is restored for
queue candidates, pull requests, or reruns.

The aggregated checks, failure rules and 80-minute aggregation deadline remain
unchanged. Polling uses conditional requests and the live rate budget, paced
for 100 candidates by the Enterprise scheduling implementation. See
[queue aggregation polling](QueueAggregationPolling.md).

## Capacity and limitations

The organization allowance is 500 total hosted jobs, including at most 50 macOS
jobs. Aggregators share that capacity with tests, scanners, audits, pull
requests and other repositories. Independent aggregation removes serialization
behind another candidate, but does not guarantee immediate runner admission or
shorter queue latency. See [the queue aggregation timeout
gotcha](../../../Gotchas/Ci/Scheduling/QueueAggregationTimeout.md).

## Verification

The resolution retains `.github/workflows/PullRequest.yml` byte-for-byte from
main commit `1619f00bf532caad262d1557bd69281179e5c497`, including the lock removal
introduced by PR #363. Git index and whitespace checks verify the conflict
repair mechanically. No local tests were run for this repair; current-head PR
checks and configured review are required separately. Native merge-group
acceptance and live queue timing remain deferred to authorized enrollment.
