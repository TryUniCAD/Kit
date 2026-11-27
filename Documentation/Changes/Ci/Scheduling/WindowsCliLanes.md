# Separate Windows CLI lanes

The budget below assumes the Team plan's 60 concurrent jobs and 5 macOS jobs. The organisation now has Enterprise limits of 500 and 50; see [four candidate lane sets](EnterpriseLaneSets.md) for the current lanes and budget.

## Behavior

The four `Research CLI Windows compatibility / shard-N` jobs now use their own `Kit-windows-cli-shard-1` to `shard-4` concurrency lanes.
Before, they shared `Kit-windows-shard-1` to `shard-4` with the Windows platform shards of the complete suite (`Test suite / Platform (windows-2025) / shard-N`).
Each lane runs one job at a time across every queue candidate (`queue: max`), so each candidate occupied every Windows lane for about 8.6 minutes.
That made the Windows lanes the heaviest per candidate, ahead of the Linux test, macOS and `Kit-linux-*` lanes.

| Lane, per candidate | Before | After |
| --- | --- | --- |
| `Kit-windows-shard-1`–`4` | CLI shard 2.4–2.7 + platform shard 5.7–6.2 = about 8.6 min | platform shard about 6.0 min |
| `Kit-windows-cli-shard-1`–`4` | — | CLI shard about 2.6 min |
| `Kit-windows-shard-5` | audit platform shards | unchanged |

Minutes are median job durations for merge-group candidates on 26 November 2026 after PR #347.

No job, check name, test, roster, report or allowlist entry changes.
Every per-case report check still runs: each CLI shard publishes its roster and outcomes, and `Research CLI Windows compatibility` still requires every collected case exactly once.
Only the CLI shards' concurrency group changes.

`.github/CiResources.json` records the four lanes as `WindowsCompatibility`.
The cooperating budget becomes 32 jobs: 16 Linux, 5 Windows platform, 4 Windows CLI, 5 macOS and 2 control, within the Team plan's 60 concurrent hosted jobs.
The scheduler's budget check reads only the existing fields, so native shard expansion behaves as before.
Windows runner minutes do not change; at most four more Windows jobs run at the same time.

## Alternatives

Folding each CLI shard into its platform shard job would save one runner setup per lane, but the combined job would still take about 7–8 minutes per candidate.
It would also rename or remove the required `Research CLI Windows compatibility / shard-N` checks, which needs a staged allowlist change.
Putting the CLI shards on the fifth Windows lane would load it with about 10 minutes per candidate.

## Verification

Durations come from the GitHub Actions jobs API for all merge-group runs created after 09:20 UTC on 26 November 2026.
The scheduler process cases and Zizmor pass locally with the new marker field.
Lane timings after this change need a merge-group candidate, which only an authorized enqueue produces.
