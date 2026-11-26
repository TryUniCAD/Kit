# Deterministic Windows research cases

## Task and behaviour

Task `CI-WINDOWS-FLAKES` is owned by the implementation agent for this PR. It is part of the effort to keep merge-queue time under ten minutes.
Its scope is the Windows platform shard flakes that ejected queue candidates between 22 and 26 November 2026.
No test is skipped, retried, marked xfail or deleted, and no assertion is weakened.
The workflows, phase allocation and CI scripts are unchanged.

| Case | Root cause | Fix |
| --- | --- | --- |
| `ProviderCleanupTests::CheckCleanup[parentexit-None]` and `[descendant-provider_timeout]` | `WindowsProcess.finish()` treated an empty job list as proof of exit, but a killed process leaves the list before it is signalled. This is a product bug: callers could see a live descendant that still held open handles. | `signal(9)` and `finish()` hold `SYNCHRONIZE` handles to job members before each termination, then wait for every held handle to be signalled within the existing five-second deadline. |
| `CircleQueueTests` and `DiscoveryQueueTests` PowerShell `TimeoutExpired` after 15 s | The runner's first `Add-Type` compile is cold. Every failure was the shard's first compile. | `WarmProgress` runs the same compile once per pytest process with a 120-second fail-closed bound. The per-case 15-second limit is kept. |
| `WindowsRearmTests::CheckRearm` | Application workers set their deadline one second before the supervisor's `CTRL_BREAK_EVENT` at `stop_at`, which was too little time to record the timeout. When it ran out, the session ended as `retry`. This is a product bug. | The new `ApplicationProtocol.STOP_MARGIN_SECONDS` (3 s) is shared by the SOLIDWORKS readback worker, the Fusion application worker, the Fusion continuous fixture and the protocol fixture. |
| `OwnerRestartTests::CheckOwnerBoot[claim]` `ReadParent.ps1` `TimeoutExpired` after 15 s | The runner's first PowerShell CIM/WMI process query is cold. | `WarmParent` runs the same query once per pytest process with a 120-second fail-closed bound. The per-observation 15-second limit is kept. |

See the gotchas for [empty jobs before exit](../../../Gotchas/Research/WindowsJobEmptyBeforeExit.md),
[the application worker deadline margin](../../../Gotchas/Research/Workers/SolidWorks/ReadbackDeadlineMargin.md),
[the cold readback compile](../../../Gotchas/Ci/Windows/ReadbackFixtureStartupTimeout.md) and
[the cold owner parent query](../../../Gotchas/Ci/Windows/OwnerParentQueryColdStart.md).

`Cli/NativeTests::CheckNativeStop[CTRL_C_EVENT]` is not changed.
Its only two failures, with 61 s elapsed, came from [PR #271's own queue candidate](https://github.com/TryUniCAD/Kit/actions/runs/45193381516/job/137758518302) and [PR #272's candidate built on it](https://github.com/TryUniCAD/Kit/actions/runs/45193382355/job/137757919738).
That candidate did not yet call `EnableCtrlInput` before starting `kit.exe`, so the launcher inherited ignored Ctrl+C input.
PR #271 added that call before merging, and all eight later runs in the sampled reports passed.

## Evidence

Failing jobs: [45824321635](https://github.com/TryUniCAD/Kit/actions/runs/45824321635/job/139925086000) and
[45108978621](https://github.com/TryUniCAD/Kit/actions/runs/45108978621/job/137476954639) for cleanup;
[45824325263](https://github.com/TryUniCAD/Kit/actions/runs/45824325263/job/139924989665),
[45175300556](https://github.com/TryUniCAD/Kit/actions/runs/45175300556/job/137695305312),
[45174474097](https://github.com/TryUniCAD/Kit/actions/runs/45174474097/job/137692603899) and
[45099506820](https://github.com/TryUniCAD/Kit/actions/runs/45099506820/job/137447175592) for readback;
[45195833207](https://github.com/TryUniCAD/Kit/actions/runs/45195833207/job/137766584419),
[45165853352](https://github.com/TryUniCAD/Kit/actions/runs/45165853352/job/137663519459) and
[45098329814](https://github.com/TryUniCAD/Kit/actions/runs/45098329814/job/137443411490) for rearm;
[45185561672](https://github.com/TryUniCAD/Kit/actions/runs/45185561672/job/137731359842) for the owner parent query.
The cleanup failure after PR #285 compared creation identities, so a reused PID is excluded.
The timing distributions come from 92 platform shard `Report.jsonl` artifacts.

## Verification and limits

These cases run only on Windows and only in the merge queue.
On Linux, Ruff, Black, Pyright, Mypy and the repository policy checks pass, and the cases collect and skip as before.
None of the Windows fixes has run on Windows yet. A queue candidate that includes this change provides the first native evidence.
The Fusion application worker and the continuous fixture run only on macOS hosts. Their margin change is checked only by the macOS platform shards in the queue.
