# Native compatibility scheduling

The workflow-quality policy job now runs repository contract checks separately from native-file compatibility. Three parallel native groups retain the complete SOLIDWORKS, Parasolid and rationale test paths, Python 3.11, frozen dependencies and ten-minute job limits. No assertion, test path or acceptance gate is removed.

Merge candidate `06b002441448d2e961629215cdc09768ea8b1530` exceeded the combined job's ten-minute limit. Its contract checks passed 406 cases in 29.21 seconds; native checks passed 498 cases with 159 recorded skips in 541.39 seconds. Setup and finalization exhausted the remaining budget. GitHub's annotation explicitly reported the execution deadline.

The new groups are mandatory merge-candidate checks in the phase registry consumed by the CI allowlist. Queue aggregation process coverage includes success, failure, cancellation, timeout and skipped outcomes for each group. PR validation defers the groups to merge-candidate acceptance. Current candidate acceptance remains required; the failed candidate is retained as evidence.
