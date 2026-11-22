# Stage only the Boss collector source fixture

The Windows Boss source-admission process fixture now copies the eighteen files pinned by the collector instead of every Python, C# and PowerShell file beneath the automation tree.
The existing readback fixture contributes one additional launcher file.
Clean admission, modified collector, modified launcher and both Git replacement cases retain their original assertions.
No process deadline, native launch rule or source-integrity check changes.

Merge candidate `9af448c903add50a72a2bbb02809dddcbf442a0c` failed when `git add re` exceeded its twenty-second deadline in `CheckBossSource[launcher-False]`.
The previous copy selected 535 automation files. The repaired fixture requires nineteen files in total.
This failure removed PR #265 from the merge queue; it was not a Fusion decoding failure.

[Failed Windows job](https://github.com/TryUniCAD/Kit/actions/runs/45078729462/job/137382013976)

The changed fixture remains in the existing Windows platform shard and complete merge-queue suite.
Windows confirmation requires a new merge-group run. Local source inspection does not substitute for that result.

[Fixture scope gotcha](../../../../Gotchas/Ci/Windows/BossSourceFixtureScope.md)
