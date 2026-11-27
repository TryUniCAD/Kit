# Manual audits share candidate capacity

Reducing native queue build concurrency does not limit `workflow_dispatch` audits.
Two full audits began at 14:27:45 and 14:30:11 UTC on 23 November 2026 while PR 272 awaited acceptance.
Their macOS jobs shared the hosted five-job allowance with the merge candidate.
The candidate plan finished at 14:33:37; its final macOS shard started at 14:46:07, a twelve-minute-thirty-second wait.

The [research audit](https://github.com/TryUniCAD/Kit/actions/runs/45194452163),
[main audit](https://github.com/TryUniCAD/Kit/actions/runs/45194886159), and
[candidate](https://github.com/TryUniCAD/Kit/actions/runs/45195261181) retain the job timestamps.
Obsolete-candidate cleanup deliberately preserves legitimate manual audits.

Use the current main-branch harness, serialize audit requests, and admit them after native queue work ends.
Bound their native work to the fifth shared lane so an arriving candidate still has four lanes available.
Do not cancel unrelated audits or remove their acceptance checks to free capacity.
The [runner budget change](../../../Changes/Ci/RunnerBudgetScheduling.md) records rollout and verification limits.
