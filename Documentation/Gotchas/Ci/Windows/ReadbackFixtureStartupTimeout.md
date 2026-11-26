# A Windows readback fixture can time out before its expected rejection

Expected: `CheckRoundQueue[binding]` reaches the fixture's native-progress rejection and verifies its reason.
Observed: in [the supplementary feature-session audit](https://github.com/TryUniCAD/Kit/actions/runs/44912719271/job/136872129804), the PowerShell fixture command exceeded its 15-second limit first; the suite recorded 156 passes and one failure.
The [independent full audit](https://github.com/TryUniCAD/Kit/actions/runs/44912221736) of the same source `72207ec5684d89bf98023427ce4f49eac3a5d122` passed every Windows case and all acceptance gates.

## Cause

The timeout is the runner's first `Add-Type` compile, not a slow fixture.
Across 92 Windows platform shard reports from 22–26 November 2026, the first `CircleQueueTests` or `DiscoveryQueueTests` case in a shard took 1.6–19.4 s.
All four failures (16.8, 17.1, 17.8 and 19.4 s) and the only two passes above 9 s were that first case.
The 345 later cases had p50 1.8 s, p99 5.5 s and max 8.4 s, even though each one starts a new PowerShell process and compiles again.
The cold start is in the runner (compiler image, framework assemblies and new-binary scanning), not in each PowerShell process.

## Workaround

`WarmProgress` runs the same `ProgressFixture.ps1` compile with `-CompileOnly` once per pytest process, before the first readback listener starts.
It has a 120-second fail-closed bound.
The per-case 15-second limit now covers only warm compiles, and its assertions are unchanged.
If a warm case times out again, diagnose the process boundary instead of widening the limit.
