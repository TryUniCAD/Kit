# Windows owner parent observations use native snapshots

Expected: `ReadParent` returns a process parent without starting a management shell. Linux retains its existing `ps` subprocess timeout; Windows performs the native snapshot call directly, without a subprocess deadline.

Observed: the prior Windows implementation started PowerShell and queried `Win32_Process` through CIM/WMI. Its first runner query exceeded the per-observation deadline, so a per-process warm-up repeated that cold dependency with a separate 120-second failure bound. The historical failure was [`OwnerRestartTests::CheckOwnerBoot[claim]`](https://github.com/TryUniCAD/Kit/actions/runs/45185561672/job/137731359842); across 46 shard reports the test usually took about 10 seconds, with a tail of 14.1, 17.5 and 26.2 seconds. Only the 26.2-second run failed.

Workaround: Windows observations now enumerate a fresh Toolhelp process snapshot in the caller process. The snapshot is never cached, so each owner check sees current process ownership. Normal enumeration completion returns `None` for a missing process; other native failures raise. Linux retains its `ps` implementation. Native Windows execution remains to be verified by the merge-queue platform shard.
