# Parallel queue gates

## Ownership

Task CI post-shard gate tail; owner Hoplite; scope is the redundant acceptance dependency after complete-suite reporting.
Dependencies are the existing exact-once report and direct acceptance inputs.
Delivery is this change's normal PR.
Exit requires current-head PR checks and configured review.
Candidate timing requires separately authorized queue enrollment.

## Behavior

Merge queue acceptance no longer waits for the compatibility job named `Run the complete test suite`.
Both jobs still require the successful plan, every Linux shard and the exact-once completeness report.
Acceptance also retains every existing platform and security dependency.
The compatibility job, its three-input assertion and its aggregate registration remain unchanged.
CI aggregation still requires both jobs and rejects either job's failure.

The post-shard dependency depth changes from three jobs to two before aggregation:

- Before: shards, report, compatibility job, acceptance.
- After: shards, report, then compatibility job and acceptance in parallel.

Every check name and completeness rule remains.
No new check-writing permission, synthetic status or reporter trust exception is introduced.
The report's artifact and dependency-cache publication remain unchanged.
Further physical job merging would require a separate reported-check design and trusted-base rollout.

## Timing evidence

The [PR #375 candidate](https://github.com/TryUniCAD/Kit/actions/runs/46005349452) spent 17 minutes 38 seconds before final CI aggregation completed.
After its final shard, three sequential jobs spent 288 seconds waiting for runners and 49 seconds executing.
The report waited 37 seconds and ran 42 seconds.
The compatibility job waited 135 seconds and ran three seconds.
Acceptance waited 116 seconds and ran four seconds.

Parallel pickup removes one sequential runner allocation from this dependency path.
About two minutes could be saved under similar scheduling, but actual savings depend on provider allocation and concurrent work.
No post-change speedup is claimed before a candidate executes.

## Verification

The new process scenarios execute the actual workflow gate command with success, failure, cancellation, skip, timeout and pending completeness inputs.
Existing aggregation process scenarios still require every native check, including the compatibility job.
These scenarios run through the complete shared suite, its shards and its exact-once report.

Local formatting, syntax and whitespace checks passed.
No local tests ran under repository policy.
Remote PR checks, configured review and candidate acceptance remain pending.
