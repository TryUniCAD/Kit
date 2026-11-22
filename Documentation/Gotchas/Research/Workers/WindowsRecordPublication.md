# Windows record publication can precede compatible handle acquisition

## Expectation

An atomically published application response should be ready for a protected read when its destination path exists.

## Actual behavior

A native Windows audit rejected `CheckRoundQueue[binding]` with application-record error `32` instead of its intended progress-binding rejection.
The log does not identify the contested path or handle owner.
See [the Windows job](https://github.com/TryUniCAD/Kit/actions/runs/45065176759/job/137340060510).

An initial protected open can conflict with a publisher or another process's still-open write/delete handle.
Windows keeps sharing restrictions until the conflicting handle closes, including during a rename handoff.
This is consistent with the observed failure, rather than a directly traced publisher identity.
See [CreateFileW sharing rules](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).

## Workaround

Preserve `FILE_SHARE_READ` and acquire fresh protected handles before exposing bytes.
Classify only an initial sharing violation as busy, retaining the native code and path.
The queue response poll can retry that conflict within its original deadline.
Keep identity errors and every error after handle acquisition fail-closed.
Do not add write/delete sharing or turn arbitrary I/O errors into successful reads.

Native process coverage publishes a response while a real writable handle remains open.
A client marker witnesses the actual blocked acquisition before the fixture releases the handle.
A second case retains the handle and verifies the unchanged bounded deadline and fencing.
These process checks do not establish native CAD acceptance.

See [the repair](../../../Changes/Ci/AttributionQueueRepair.md)
and [held-read identity](WindowsPathAndHandleTimes.md).
