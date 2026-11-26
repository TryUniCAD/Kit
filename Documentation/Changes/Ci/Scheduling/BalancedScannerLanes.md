# Balanced merge-queue scanner lanes

## Behavior

Merge-group jobs on the eight shared `Kit-linux-*` lanes are reassigned so lanes 0–5 each carry about the same work per candidate.
Before, lanes 0–3 carried 5.4–6.8 minutes of serial work per candidate, while lanes 4 and 5 carried 1.1 and 2.3 minutes.
Each lane runs one job at a time across every candidate (`queue: max`), so the heaviest lane sets how quickly candidates can finish behind each other.
Lanes 6 and 7 carry less queue work than before, because manual audits run there.

Pull-request runs of the jobs that also had a `Kit-linux-*` lane (Ruff, Black, Pyright, Mypy, Python steering, Zizmor and actionlint) now use their own `Kit-pull-<job>` lanes.
Before, a PR's Mypy and Python steering waited behind queue candidates' work on `Kit-linux-7`, and its Pyright behind `Kit-linux-6`.
Each PR lane still runs one job at a time, so PR jobs remain bounded: `.github/CiResources.json` records them as `PullRequest: 7`, which makes the cooperating budget 35 jobs, within the Team plan's 60 concurrent hosted jobs.
Merge-group runs of Pyright, Mypy and Python steering keep `Kit-linux-6` and `Kit-linux-7`.

No job, check name, test, scanner, threshold or allowlist entry changes.
Only `concurrency.group` values move.
Manual audit jobs keep lanes 6 and 7, and test shards keep the separate `Kit-test-linux-*` lanes.
The `Kit-linux-*` lanes exist to cap how many heavy Linux jobs run at once within the [shared runner budget](../RunnerBudgetScheduling.md) and to keep lanes 0–5 free of manual audits; both still hold.

`Native file compatibility` shards select their lane from a new `lane` matrix value (1–4) instead of their `index`, which still selects the shard's cases.

## Lane mapping

Minutes are median job durations (setup to finish) per candidate: merge-group candidates after PR #347 (26 November, 09:20–10:15 UTC) / Nov 23–25 candidates.

| Lane | Before | Minutes | After | Minutes |
| --- | --- | --- | --- | --- |
| `Kit-linux-0` | Analyze python, CycloneDX SBOM, OOM witness, Native shard-1, CI policy | 6.8 / 8.0 | Analyze python, Bandit, OSV-Scanner | 4.5 / 4.8 |
| `Kit-linux-1` | Analyze actions, Bandit, Native shard-2, Qualify patches, dlint | 5.9 / 7.5 | Analyze java-kotlin, Native shard-1, Gitleaks, OOM witness | 4.6 / 6.4 |
| `Kit-linux-2` | Analyze java-kotlin, Gitleaks, Native shard-3, Semgrep | 5.5 / 7.6 | Grype, Native shard-2, Scorecard | 4.6 / 5.8 |
| `Kit-linux-3` | Analyze javascript-typescript, Grype, Native shard-4, pip-audit | 5.4 / 6.4 | Qualify patches, Native shard-3, Analyze actions, Safety | 4.7 / 6.0 |
| `Kit-linux-4` | OSV-Scanner, Safety | 1.1 / 1.2 | Native shard-4, Checkov, dlint, pip-audit | 4.6 / 5.7 |
| `Kit-linux-5` | Checkov, Scorecard | 2.3 / 2.5 | Semgrep, Analyze javascript-typescript, CI policy, CycloneDX SBOM, Trivy | 4.6 / 5.2 |
| `Kit-linux-6` | Pyright, Trivy, detect-secrets | 3.4 / 3.8 | Pyright, detect-secrets, Syft | 3.2 / 3.6 |
| `Kit-linux-7` | Mypy, Python steering, Syft, TruffleHog | 3.4 / 3.7 | Mypy, Python steering, TruffleHog | 3.0 / 3.2 |

The heaviest lane drops from 6.8 to 4.7 minutes per candidate on the post-#347 medians.
The older medians include slower native shards (2.2–2.5 minutes), which is why lane 1 shows 6.4 there.

## Limits

Lane serialization is only one constraint.
In the first four candidates after PR #347 (23.7, 32.5, 38.8 and 44.5 minutes), the last jobs to finish were the Windows platform shards.
Each `Kit-windows-shard-N` lane carries a Windows research CLI shard (about 2.6 minutes) and a Windows platform shard (about 6.0 minutes) per candidate, so it is now the heaviest lane.
The `Kit-test-linux-*` lanes come next: the runtime planner gave each candidate seven shards of 5.5–8 minutes, so lanes 0–6 each carry about 6 minutes per candidate and lane 7 stays idle.
Candidates move through those lanes in lockstep.
On every test lane, PR #347's shard waited 12–15 minutes while the #349 shard and then the #297 shard ran ahead of it.
macOS platform lanes carry about 6.2 minutes per candidate.
This change does not touch the test lanes because the planner already balances them; using the idle eighth lane needs an eight-shard plan, which is a planner change.
This change alone is not expected to shorten candidate wall time much until the Windows lanes are also relieved.
See [the lane pacing gotcha](../../../Gotchas/Ci/Scheduling/HeaviestLanePacing.md).

The single queue `CI Agg` slot stays.
It delayed 3 of 29 successful candidates from 23–26 November by 4.6–6.6 minutes; across all 29 the median delay was 0.4 minutes.
Polling per candidate would exceed the repository's `GITHUB_TOKEN` rate limit at three to four concurrent candidates.
See [the aggregation slot gotcha](../../../Gotchas/Ci/Scheduling/QueueAggregationSlot.md).

## Verification

Durations come from the GitHub Actions jobs API for all merge-group runs in the windows above.
The before and after sets contain the same 29 jobs.
The repository's CI policy, report and queue aggregation process cases pass locally, and Zizmor reports no findings.
The merge-group lane timings after this change still need a candidate run, which only an authorized enqueue produces.
