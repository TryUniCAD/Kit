# Balanced merge-queue scanner lanes

## Behavior

Merge-group jobs on the eight shared `Kit-linux-*` lanes are reassigned so each lane carries about the same work per candidate.
Before, lanes 0–3 carried 5.4–6.8 minutes of serial work per candidate, while lanes 4 and 5 carried 1.1 and 2.3 minutes.
Each lane runs one job at a time across every candidate (`queue: max`), so the heaviest lane sets how quickly candidates can finish behind each other.

No job, check name, test, scanner, threshold or allowlist entry changes.
Only the `concurrency.group` lane number of merge-group jobs moves.
Manual audit jobs keep lanes 6 and 7, PR-phase jobs keep their lanes, and test shards keep the separate `Kit-test-linux-*` lanes.
The lanes still exist for the same reason: they cap how many heavy Linux jobs run at once within the [shared runner budget](../RunnerBudgetScheduling.md), and they keep lanes 0–5 free of manual audits.

`Native file compatibility` shards select their lane from a new `lane` matrix value (1–4) instead of their `index`, which still selects the shard's cases.

## Lane mapping

Minutes are median job durations (setup to finish) per candidate: merge-group candidates after PR #347 (26 November, 09:20–10:15 UTC) / Nov 23–25 candidates.

| Lane | Before | Minutes | After | Minutes |
| --- | --- | --- | --- | --- |
| `Kit-linux-0` | Analyze python, CycloneDX SBOM, OOM witness, Native shard-1, CI policy | 6.8 / 8.0 | Analyze python, Gitleaks, OOM witness | 4.3 / 5.1 |
| `Kit-linux-1` | Analyze actions, Bandit, Native shard-2, Qualify patches, dlint | 5.9 / 7.5 | Analyze java-kotlin, Native shard-1, OSV-Scanner | 4.0 / 5.2 |
| `Kit-linux-2` | Analyze java-kotlin, Gitleaks, Native shard-3, Semgrep | 5.5 / 7.6 | Grype, Native shard-2, Safety | 4.3 / 5.4 |
| `Kit-linux-3` | Analyze javascript-typescript, Grype, Native shard-4, pip-audit | 5.4 / 6.4 | Qualify patches, Native shard-3, Analyze actions | 4.1 / 5.3 |
| `Kit-linux-4` | OSV-Scanner, Safety | 1.1 / 1.2 | Native shard-4, Checkov, dlint, Syft | 4.4 / 5.4 |
| `Kit-linux-5` | Checkov, Scorecard | 2.3 / 2.5 | detect-secrets, Semgrep, Analyze javascript-typescript, pip-audit | 4.2 / 5.0 |
| `Kit-linux-6` | Pyright, Trivy, detect-secrets | 3.4 / 3.8 | Pyright, CI policy, Scorecard, CycloneDX SBOM | 4.1 / 4.5 |
| `Kit-linux-7` | Mypy, Python steering, Syft, TruffleHog | 3.4 / 3.7 | Mypy, Python steering, TruffleHog, Trivy, Bandit | 4.4 / 4.8 |

The heaviest lane drops from 6.8 to 4.4 minutes per candidate (8.0 to 5.4 on the older medians).
Lanes 6 and 7 stay slightly lighter because PR-phase Pyright, Mypy and Python steering and manual audits also use them.

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

## Verification

Durations come from the GitHub Actions jobs API for all merge-group runs in the windows above.
The before and after sets contain the same 29 jobs.
The repository's CI policy, report and queue aggregation process cases pass locally, and Zizmor reports no findings.
The merge-group lane timings after this change still need a candidate run, which only an authorized enqueue produces.
