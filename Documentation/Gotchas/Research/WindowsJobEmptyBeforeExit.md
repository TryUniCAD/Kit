# An empty Windows job does not mean its processes have exited

Expected: after `TerminateJobObject` returns and the job's process list
(`JobObjectBasicProcessIdList`) is empty, every former member has exited, so
`WaitForSingleObject(process, 0)` reports it as signalled.

Actual: termination is asynchronous. A process leaves the job's active list
when its last thread starts process exit. Handle-table rundown and
address-space teardown come later, and only then is the process object
signalled. In that window `WindowsProcess.finish()` returned while a killed
descendant was still unsignalled and still held its open handles.
[`ProviderCleanupTests::CheckCleanup[parentexit-None]`](https://github.com/TryUniCAD/Kit/actions/runs/45824321635/job/139925086000)
saw that exact process, matched by creation time and not a reused PID, still
live after cleanup. [The `descendant` case](https://github.com/TryUniCAD/Kit/actions/runs/45108978621/job/137476954639)
failed the same way.
Microsoft documents that [`TerminateProcess` is asynchronous](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-terminateprocess)
and that callers must wait on the process handle to know it has terminated.

Workaround: before each `TerminateJobObject`, open a `SYNCHRONIZE` handle to
every listed member and confirm it with `IsProcessInJob`. After the list is
empty, wait on every held handle within the same deadline. A held handle also
prevents the PID from being reused. A process that is created and fully exits
between two snapshots can still be missed. The first snapshot runs before the
first termination, so every process that was alive when cleanup started is
covered.
