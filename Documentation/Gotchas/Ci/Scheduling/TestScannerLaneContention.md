# Test and scanner lane contention

Eight test matrix slots do not imply eight tests can execute together when security and policy jobs use the same concurrency keys. In [PR 279’s candidate](https://github.com/TryUniCAD/Kit/actions/runs/45365569812), shard 3 waited 18 minutes 47 seconds after planning before its 7 minute 33 second execution.

Use separate bounded test and scanner lane namespaces within the actual organization allowance. Increasing matrix fanout alone does not remove a shared concurrency-key bottleneck. The organization API reported Team on 24 November 2026; the older Free-plan observation is historical. Team allowed sixty standard hosted jobs, with five macOS jobs. The organization has since moved to Enterprise, which allows 500 concurrent hosted jobs, with 50 macOS jobs, according to [GitHub’s limits](https://docs.github.com/en/actions/reference/limits).

Separate namespaces do not help a second candidate, because every candidate still shares one lane per group.
The [candidate lane sets](../../../Changes/Ci/Scheduling/CandidateLaneSets.md) gave a second candidate its own Linux and Windows lanes; macOS could not get a second set within Team's five-job cap.
The [four candidate lane sets](../../../Changes/Ci/Scheduling/EnterpriseLaneSets.md) now give four candidates their own lanes for every heavy job, including macOS.
A lane set only helps while the live queue builds no more candidates than there are sets.

Retain audit admission and all acceptance gates. Live queue build limits remain separate configuration; lowering speculative builds requires an administrator’s settings update. See [the change entry](../../../Changes/Ci/Scheduling/SeparateTestLanes.md).
