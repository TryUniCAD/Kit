# Deterministic Windows research cases

## Task and behaviour

Task `CI-WINDOWS-FLAKES` is owned by the implementation agent for this PR. It is part of the effort to keep merge-queue time under ten minutes.
Its scope is the three Windows platform shard flakes that ejected queue candidates between 22 and 26 November 2026.
No test is skipped, retried, marked xfail or deleted, and no assertion is weakened.
The workflows, phase allocation and CI scripts are unchanged.

| Case | Root cause | Fix |
| --- | --- | --- |
| `ProviderCleanupTests::CheckCleanup[parentexit-None]` and `[descendant-provider_timeout]` | `WindowsProcess.finish()` treated an empty job list as proof of exit, but a killed process leaves the list before it is signalled. This is a product bug: callers could see a live descendant that still held open handles. | `signal(9)` and `finish()` hold `SYNCHRONIZE` handles to job members before each termination, then wait for every held handle to be signalled within the existing five-second deadline. |
| `CircleQueueTests` and `DiscoveryQueueTests` PowerShell `TimeoutExpired` after 15 s | The runner's first `Add-Type` compile is cold. Every failure was the shard's first compile. | `WarmProgress` runs the same compile once per pytest process with a 120-second fail-closed bound. The per-case 15-second limit is kept. |
| `WindowsRearmTests::CheckRearm` | The readback worker's deadline left one second before the supervisor's `CTRL_BREAK_EVENT` at `stop_at` to record the timeout. When that ran out, the session ended as `retry`. This is a product bug. | The readback worker stops dispatch at `stop_at - 3`. |

See the gotchas for [empty jobs before exit](../../../Gotchas/Research/WindowsJobEmptyBeforeExit.md),
[the readback deadline margin](../../../Gotchas/Research/Workers/ReadbackDeadlineMargin.md) and
[the cold readback compile](../../../Gotchas/Ci/Windows/ReadbackFixtureStartupTimeout.md).

## Evidence

Failing jobs: [45824321635](https://github.com/TryUniCAD/Kit/actions/runs/45824321635/job/139925086000) and
[45108978621](https://github.com/TryUniCAD/Kit/actions/runs/45108978621/job/137476954639) for cleanup;
[45824325263](https://github.com/TryUniCAD/Kit/actions/runs/45824325263/job/139924989665),
[45175300556](https://github.com/TryUniCAD/Kit/actions/runs/45175300556/job/137695305312),
[45174474097](https://github.com/TryUniCAD/Kit/actions/runs/45174474097/job/137692603899) and
[45099506820](https://github.com/TryUniCAD/Kit/actions/runs/45099506820/job/137447175592) for readback;
[45195833207](https://github.com/TryUniCAD/Kit/actions/runs/45195833207/job/137766584419),
[45165853352](https://github.com/TryUniCAD/Kit/actions/runs/45165853352/job/137663519459) and
[45098329814](https://github.com/TryUniCAD/Kit/actions/runs/45098329814/job/137443411490) for rearm.
The cleanup failure after PR #285 compared creation identities, so a reused PID is excluded.
The readback timing distribution comes from 92 platform shard `Report.jsonl` artifacts.

## Verification and limits

These cases run only on Windows and only in the merge queue.
On Linux, Ruff, Black, Pyright and Mypy pass, and the cases collect and skip as before.
None of the three fixes has run on Windows yet. A queue candidate that includes this change provides the first native evidence.
Two Windows flakes outside this scope remain: `OwnerRestartTests::CheckOwnerBoot[claim]` (`ReadParent.ps1` 15 s timeout) and `Cli/NativeTests::CheckNativeStop[CTRL_C_EVENT]`.
