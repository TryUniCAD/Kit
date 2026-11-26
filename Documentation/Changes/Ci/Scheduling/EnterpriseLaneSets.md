# Enterprise hosted concurrency

## Ownership

Task CI Enterprise capacity; owner PR #363; delivery https://github.com/TryUniCAD/Kit/pull/363. Scope is hosted scheduling, shard parallelism and the desired merge queue manifest. Dependencies are the existing paced queue poller, trusted-base resource rollout and separate administrator activation. Exit requires current-head PR checks and configured approval; live speed and merge acceptance require a separately authorized candidate.

## Behavior

Enterprise provides 500 total concurrent standard hosted jobs, including at most 50 macOS jobs. The organization API confirmed Enterprise on 26 November 2026. All operating systems, PRs, candidates, audits and other repositories share these limits; macOS is included in 500 rather than added to it.

Job-level shared concurrency lanes are removed from MergeQueue, PullRequest aggregation, PythonQuality, PythonSteering and WorkflowQuality. Candidate checks and independent PR checks can execute concurrently. Matrix max-parallel throttles are removed. Linux runtime planning can request up to 256 shards, GitHub's matrix ceiling, instead of eight; actual count still depends on measured durations and collected cases. Existing workflow-level candidate isolation, superseded-PR cancellation, manual audit admission, obsolete-candidate cleanup, platform rosters, exact coverage reports, acceptance dependencies and all security gates remain enabled.

The version 5 resource marker records Enterprise, Total 500, Macos 50 and Control 2. These describe provider capacity, not private runner reservations. The selector retains versions 1–4 for rollout from older bases. Workflows stop requesting an ancestor-count lane prefix; the legacy selector remains compatible with earlier workflow revisions.

## Desired configuration

The manifest requests GitHub's maximum build concurrency of 100 and maximum merge group of 100, minimum group one, no minimum-entry wait, ALLGREEN and a 90-minute response timeout. The expansion selector accepts integer build limits 1–100 only with minimum one and wait zero. Aggregation pacing divides available API budget across 100 candidate pollers while preserving conditional requests and the existing reserve.

The former four-set proposal and its 323-job scenario are superseded. GitHub enforces actual organization capacity and queues excess work. A hundred candidates can request up to 500 macOS shards, so full build admission does not guarantee faster completion or an empty queue. No throughput or absence of stalls is claimed. Inspect runner waiting time and candidate completion latency after activation. Larger runners remain excluded because they are billed even for public repositories.

Live Protect ruleset 25490615 was read on 26 November: build concurrency 25, merge minimum two, wait ten minutes, maximum ten merged entries, response timeout 60 minutes. An administrator must update that existing queue rule separately after this PR lands, preserving all unrelated protections. The PR changes no live settings and enrolls no candidate. PR #359 independently removes the aggregation bottleneck; removing the job lock here provides the same concurrency while preserving candidate workflow isolation.

## Verification

Base inspected: main 6dcee725b861fd410aaea3e829c8dc3692664fa3. Existing scheduling process coverage is updated for the Enterprise marker, over-capacity rejection, legacy markers, build limits five and 100, and rejection above 100. Existing real aggregation process cases cover pacing for 100 pollers, conditional requests and rate-limit recovery. These cases run through the existing merge-queue planner, suite shards and completeness report. Local tests were not run for this revision under repository policy; previous-head results are not evidence for this change. Current-head PR CI, configured review, live timing and queue acceptance remain pending.

See [runner limits](https://docs.github.com/en/actions/reference/limits), [merge queue limits](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue), and [queue aggregation pacing](QueueAggregationPolling.md).
