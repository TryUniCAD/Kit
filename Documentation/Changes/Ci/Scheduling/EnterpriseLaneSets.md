# Four candidate lane sets for the Enterprise runner budget

## Behavior

The organisation moved from GitHub Team to Enterprise.
GitHub-hosted runners now allow 500 concurrent jobs, at most 50 of them macOS, up from 60 and 5 ([GitHub limits](https://docs.github.com/en/actions/reference/limits)).
Merge-group candidates now run every heavy job in one of four lane sets, so four candidates build fully in parallel.
The [two candidate lane sets](CandidateLaneSets.md) covered only Linux and Windows platform shards 1–4.
Every platform shard, including macOS and Windows shard 5, and the Windows research CLI shards now has per-set lanes as well.

| Lane family | Set A | Sets B, C, D |
| --- | --- | --- |
| Linux tests | `Kit-test-linux-0`–`7` | `Kit-B-test-linux-0`–`7`, `Kit-C-…`, `Kit-D-…` |
| Linux scanners, policy, Pyright, Mypy, steering | `Kit-linux-0`–`7` | `Kit-B-linux-0`–`7`, `Kit-C-…`, `Kit-D-…` |
| Windows platform shards 1–5 | `Kit-windows-shard-1`–`5` | `Kit-B-windows-shard-1`–`5`, `Kit-C-…`, `Kit-D-…` |
| Windows research CLI shards | `Kit-windows-cli-shard-1`–`4` | `Kit-B-windows-cli-shard-1`–`4`, `Kit-C-…`, `Kit-D-…` |
| macOS platform shards 1–5 | `Kit-macos-shard-1`–`5` | `Kit-B-macos-shard-1`–`5`, `Kit-C-…`, `Kit-D-…` |

Set A keeps the existing names.
Pull-request runs, manual audits and pushes to `main` always receive the empty prefix, so they keep using set A's audit lanes (Linux lanes 6 and 7, Windows and macOS shard 5), the `Kit-pull-*` lanes and the single `CI Agg` queue slot.

### Lane selection

`.github/scripts/Scheduling/SelectLaneSet.cjs` now takes the candidate's ancestor count modulo 4: remainder 0 selects set A, 1 selects B, 2 selects C and 3 selects D.
The queue squashes every entry into one commit on top of the previous candidate, so four consecutive candidates always land in four different sets.
The selector still runs in `Test suite / Plan` and in the `PR CI reuse` job of Workflow quality, Python quality and Python steering, and an unreadable ancestor count still fails those checks closed.
A rebuilt candidate has the ancestor count of the failed one it replaces, so the two share a set until the old run ends; this only delays work.

### Resource marker and expansion

`.github/CiResources.json` is now version 4 with `Plan: Enterprise`, `LaneSets: 4`, `Linux: 64`, `Windows: 20`, `WindowsCompatibility: 16`, `Macos: 20`, `Control: 2` and `PullRequest: 7`.
`SelectBudget.cjs` accepts the exact version 4 values and still accepts versions 1, 2 and 3, so a candidate whose trusted base has an older marker keeps native shard expansion.
`ReadExpansion.cjs` now enables shard expansion when the live ruleset builds 1 to 4 candidates, with a minimum group of 1 and no wait.
The checked-in [queue manifest](../../../../.github/MergeQueue.json) now asks for 4 builds.

## Budget

Worst case: four candidates in four sets, a manual audit, a push to `main` and four pull-request pushes at once, with every job running at the same moment.
The observed peak on 26 November 2026 was 38 concurrent pull-request-event workflow runs, about two pushes, so four pushes is twice that peak.
Each pull-request push starts at most 25 unlaned jobs: 15 in `pull_request` workflows and 10 in `pull_request_target` labelling and aggregation workflows.
Each candidate has at most 21 unlaned jobs: the `PR CI reuse` selectors, light verifiers, planning, platform aggregators, report and gate.
An audit and a `main` push add at most 10 unlaned jobs.

| Pool | Standard jobs | macOS jobs |
| --- | ---: | ---: |
| Linux candidate and audit lanes (4 × 16) | 64 | |
| Linux pull-request lanes (`Kit-pull-*`) | 7 | |
| Windows platform lanes (4 × 5) | 20 | |
| Windows research CLI lanes (4 × 4) | 16 | |
| macOS platform lanes (4 × 5) | | 20 |
| Control slots | 2 | |
| Laned subtotal | 109 | 20 |
| Unlaned candidate jobs (4 × 21) | 84 | |
| Unlaned audit and `main` push jobs | 10 | |
| Pull-request pushes (4 × 25) | 100 | |
| Total | 303 | 20 |

Counting the macOS jobs against the 500 total as well gives 323, about 65% of the allowance; macOS uses 20 of 50.
The laned subtotal, which matches how the [two-set budget](CandidateLaneSets.md) counted 59 of 60, is 109 standard and 20 macOS jobs.
Each pull-request push beyond four adds at most 25 jobs, so about 7 more simultaneous pushes fit before the total reaches 500.
Other organisation repositories share the same allowance and are not counted.
GitHub holds jobs above the limit until a runner frees, without failing them.

## Live queue settings still need an administrator

The live `main` ruleset, read back on 26 November 2026, still builds 25 candidates with a 60-minute response timeout, a minimum of 2 entries per merge, a 10-minute minimum-entry wait and up to 10 entries per merge.
Under those settings the four sets are shared by up to 25 candidates and native shard expansion stays disabled.
A repository administrator must set the existing queue rule to max entries to build 4, minimum entries to merge 1, minimum-entries wait 0 and response timeout 90 minutes, preserving every other protection.
This change does not modify repository settings.

## Unchanged

No job, check name, test, shard roster, report, phase or allowlist entry changes.
`queue: max` and `cancel-in-progress: false` stay on every lane.
Audit admission, exact-once reporting and the acceptance gate are unchanged.

## Evidence and limits

Task: CI-EnterpriseLaneSets; owner: Hoplite; scope: four lane sets for all heavy merge-group jobs under the Enterprise runner budget.
Dependency: PR #362 (two candidate lane sets).
Exit: current-head CI and configured approval, the administrator queue update, then an authorized queue run showing four candidates in four sets.

The scheduler process cases in `tests/Policy/Scheduling` run the real selector for all four remainders, pull-request, missing-commit and API-error inputs.
They check that the version 4 marker and the earlier version 3, 2 and 1 markers are accepted, that a version 4 marker with the Team macOS value or a single lane set is rejected, and that a live build limit of 5 disables expansion.
`tests/Policy` passes locally, and actionlint, zizmor, the workflow pin check and the path policy pass.
The parallel speedup still needs to be measured on four live candidates.
