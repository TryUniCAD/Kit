# Separate merge queue test lanes

The budget below assumes the Team plan's 60 concurrent jobs and 5 macOS jobs. The organisation now has Enterprise limits of 500 and 50; see [four candidate lane sets](EnterpriseLaneSets.md) for the current lanes and budget.

## Behavior

Candidate Linux test shards use eight dedicated `Kit-test-linux-*` lanes. Scanners, policy jobs, and admitted audits retain the eight `Kit-linux-*` lanes. Previously both workloads competed for the same eight lanes. Matrix size, exact-once reporting, security checks, test reuse, audit admission, and cancellation behavior are unchanged. Manual audits retain the two existing Linux audit lanes.

The resource marker records sixteen Linux lanes, five Windows lanes, five macOS lanes, and two control slots: twenty-eight cooperating jobs. The organization API reported the Team plan on 24 November 2026. Its standard hosted allowance is sixty concurrent jobs; macOS remains capped at five. Other organization jobs can still consume that allowance. Increased parallelism can increase simultaneous resource usage; this change adds no test executions or paid runner labels.

The desired queue permits two candidate builds, one minimum merge entry, and zero batching wait. Native shard expansion accepts either one or two live candidate builds, retaining the existing audit reservation and trusted-base checks. Legacy version-one resource markers remain supported for rollout. The first rollout candidate can use the separate test lanes immediately, while native expansion still follows the trusted base and live settings.

## Evidence and limits

Task: CI-QueueConcurrency; owner: Codex; scope: separate Linux worker pools and two-build configuration; dependency: merged runner-budget scheduling; delivery: this PR. Exit: current-head CI and configured approval, then separately authorized queue acceptance and measured post-rollout latency.

[PR 279 candidate run](https://github.com/TryUniCAD/Kit/actions/runs/45365569812) planned at 09:29:57 UTC. Shard 3 started at 09:48:44, then ran for 7 minutes 33 seconds. Its wait was 18 minutes 47 seconds. Other Linux shards took 6 minutes 48 seconds to 8 minutes 40 seconds. These are baseline measurements, not a demonstrated speedup.

Existing scheduler process coverage now reads the real resource marker and exercises the two-build live rule alongside unsafe settings, API errors, audit reservation, and admission paths through the complete shared suite. Remote verification and native acceptance are pending at publication. No local tests were run.

The live queue was observed with 25 candidate builds, a two-entry merge minimum, and a ten-minute wait. This PR does not mutate repository settings. An administrator must apply the desired queue parameters to the existing ruleset while preserving unrelated protections. Until then, later candidates still compete for each worker pool and native expansion remains disabled. Strict oldest-candidate priority is not supplied by job concurrency groups; GitHub queues each group by when its jobs begin waiting.

See the [queue guide](../../../../MergeQueue.md), [settings drift](../../../Gotchas/Ci/Scheduling/QueueSettingsDrift.md), and [slot contention](../../../Gotchas/Ci/Scheduling/TestScannerLaneContention.md).
