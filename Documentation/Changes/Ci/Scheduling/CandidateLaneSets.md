# Two candidate lane sets

The budget below assumes the Team plan's 60 concurrent jobs and 5 macOS jobs. The organisation now has Enterprise limits of 500 and 50; see [four candidate lane sets](EnterpriseLaneSets.md) for the current lanes and budget.

## Behavior

Merge-group candidates now run their heavy Linux and Windows jobs in one of two lane sets.
Before, every candidate competed for the same single lane per concurrency group, so a second candidate's shards and scanners waited behind the first.
Two candidates in different sets now run those jobs side by side; a third candidate shares a set with one of them and waits, as before.

| Lane family | Set A | Set B |
| --- | --- | --- |
| Linux tests | `Kit-test-linux-0`–`7` | `Kit-B-test-linux-0`–`7` |
| Linux scanners, policy, Pyright, Mypy, steering | `Kit-linux-0`–`7` | `Kit-B-linux-0`–`7` |
| Windows platform shards 1–4 | `Kit-windows-shard-1`–`4` | `Kit-B-windows-shard-1`–`4` |
| Windows platform shard 5 | `Kit-windows-shard-5` (shared) | `Kit-windows-shard-5` (shared) |
| Windows research CLI shards | `Kit-windows-cli-shard-1`–`4` (shared) | same (shared) |
| macOS platform shards | `Kit-macos-shard-1`–`5` (shared) | same (shared) |

Set A keeps the existing names, so pull-request lanes, manual audits (Linux lanes 6 and 7, native shard 5) and the queue aggregation slot are unchanged.
Set B is used only by merge-group candidates.

### Lane selection

Each candidate's set comes from the parity of its commit's ancestor count, read through the GraphQL `history.totalCount` of the merge-group head SHA.
An even count selects set A and an odd count selects set B.
The queue squashes every entry into one commit on top of the previous candidate, so consecutive candidates always differ by one ancestor and get different sets.
The value depends only on the candidate SHA, so every workflow computes the same set.
`.github/scripts/Scheduling/SelectLaneSet.cjs` does this in `Test suite / Plan` and in the `PR CI reuse` job of Workflow quality, Python quality and Python steering.
Each job exposes it as the `lanes` output (an empty string or `B-`) that every heavy concurrency group prefixes.
Pull-request, push and manual audit runs always receive the empty prefix.
An unreadable ancestor count fails the selecting job, which fails that workflow's checks closed, instead of letting jobs of one candidate split across sets.

GitHub expressions have no modulo and the run number is shared with pull-request runs, so neither alternates reliably between candidates.
Parity can still match an unfinished run: if a failed candidate is rebuilt, the rebuilt candidate has the failed one's ancestor count, and they share a set until the old run ends.
That only delays work; each lane still runs one job at a time.

## Budget

The Team plan allows 60 concurrent hosted jobs, at most 5 of them macOS ([GitHub limits](https://docs.github.com/en/actions/reference/limits)).
Worst case, with two candidates, an audit and pull-request jobs all filling every lane:

| Pool | Jobs |
| --- | --- |
| Linux candidate and audit lanes (2 × 16) | 32 |
| Linux pull-request lanes (`Kit-pull-*`) | 7 |
| Windows platform lanes (2 × 4 + shared shard 5) | 9 |
| Windows research CLI lanes (shared) | 4 |
| macOS lanes (shared) | 5 |
| Control slots | 2 |
| Total | 59 |

The total was 39 before this change.
`.github/CiResources.json` records it as version 3 with `LaneSets: 2`.
`SelectBudget.cjs` accepts versions 1, 2 and 3, so the first candidate, whose trusted base still has version 2, keeps native shard expansion.

Planning, phase, aggregation and other unlaned control jobs are not bounded by lanes, nor are other organisation workflows.
They can briefly push the organisation past 60; GitHub then holds the extra jobs until a runner frees, without failing them.

The fifth Windows lane stays shared because it is the audit and expansion lane.
Sharing it with both sets keeps the total within 60, and a fifth shard only exists when no audit is running.
The Windows research CLI lanes stay shared for the same reason.
A CLI shard takes about 2.6 minutes, and the second candidate waits longer than that for macOS anyway.

### Why macOS stays shared

The organisation can run five macOS jobs at once.
One candidate already uses four macOS shards plus the audit lane, or five shards when expanded.
A second set would need a sixth macOS job, so it cannot fit.
Splitting the five lanes between two sets would halve each candidate's macOS throughput even when it runs alone.
macOS therefore keeps one shared set: the second candidate's macOS shards run after the first candidate's.
That serial step, about 6 minutes per candidate as of PR #354, is now the main thing that separates two parallel candidates.
`CI Agg` also keeps its single queue slot for the rate-limit reasons in [the aggregation gotcha](../../../Gotchas/Ci/Scheduling/QueueAggregationSlot.md).

## Unchanged

No job, check name, test, shard roster, report, phase or allowlist entry changes.
`queue: max` and `cancel-in-progress: false` stay on every lane.
Audit admission, exact-once reporting and the acceptance gate are unchanged.

## Evidence and limits

Task: CI-CandidateLaneSets; owner: Hoplite; scope: two Linux and Windows lane sets for merge-group candidates.
Dependencies: PR #353 (balanced scanner lanes) and PR #354 (Windows CLI lanes).
Exit: current-head CI and configured approval, then an authorized queue run showing two candidates in different sets.

The scheduler process cases in `tests/Policy/Scheduling` now run the real selector for even, odd, pull-request, missing-commit and API-error inputs.
They also check that the real version 3 marker, the previous version 2 marker and the version 1 audit marker are all accepted, and that a single lane set is rejected.
actionlint, zizmor, the workflow pin check and the path policy pass locally.
The parallel speedup still needs to be measured on two live candidates.
The live queue must build at least two candidates; the manifest asks for two.
