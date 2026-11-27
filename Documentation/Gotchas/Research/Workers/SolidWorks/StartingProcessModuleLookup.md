# A starting SOLIDWORKS process may have no readable main module

Catalogue authoring checks the exact process image before looking up the
application's COM object. During the first combined shutdown replay at
`d170ae1c03ac78d32c1e9d369ccd08393603af72`, the new process had a live launch
handle and creation identity. `Process.MainModule.FileName` still raised
`NullReferenceException` before attachment, and the launcher rejected the
attempt before any model was opened.

Query the image path through the original process handle with
`QueryFullProcessImageNameW`, as the paired scope collector does. Keep the
creation time, session, expected image path and COM PID checks. Reject a query
failure and keep the launcher's exact-owner teardown policy.
[Windows process image query](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-queryfullprocessimagenamew)
