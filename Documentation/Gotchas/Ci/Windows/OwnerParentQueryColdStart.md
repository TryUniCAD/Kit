# The first owner parent query on a runner can exceed its deadline

Expected: `ReadParent.ps1` returns a process's parent PID well within the 15-second limit that `ReadParent` applies to each owner observation.

Observed: [`OwnerRestartTests::CheckOwnerBoot[claim]`](https://github.com/TryUniCAD/Kit/actions/runs/45185561672/job/137731359842) timed out after 15 seconds on its first query.
`OwnerRestartTests` is the only caller of `ReadParent` in a platform shard, so its first query is the runner's first `Get-CimInstance Win32_Process` call from PowerShell.
In 46 shard reports the test usually took about 10 s, with a tail of 14.1, 17.5 and 26.2 s.
Only the 26.2 s run failed.
This is the same first-use cost as the [cold readback compile](ReadbackFixtureStartupTimeout.md): PowerShell, the CIM client and the WMI provider host all start cold.

Workaround: `WarmParent` runs the same `ReadParent.ps1` query once per pytest process, for the test's own PID, with a 120-second bound that fails the test if exceeded.
Each observation keeps its 15-second limit and its assertions.
