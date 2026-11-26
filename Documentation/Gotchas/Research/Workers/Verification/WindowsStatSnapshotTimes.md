# Windows file snapshot timestamps

A stable file can have different `st_ctime_ns` values through Python path and
descriptor APIs. The Windows compatibility job for pull request 209 rejected
unchanged decoding artifacts because the verifier compared these values directly.
[Failed Windows job](https://github.com/TryUniCAD/Kit/actions/runs/44909982705/job/136863659801)

In CPython 3.14, `win32_xstat` preserves creation time in the path result's
`st_ctime` field. The descriptor path uses the native metadata change time.
This difference is visible in the
[path implementation](https://github.com/python/cpython/blob/v3.14.0/Modules/posixmodule.c#L2133)
and the
[descriptor implementation](https://github.com/python/cpython/blob/v3.14.0/Python/fileutils.c#L1028).
Removing change time or identity checks would conceal real input changes.

The verifier reads Windows snapshots with one native handle API for every view.
It compares volume identity, the complete 128 bit file identity, size, creation
time, last write time, metadata change time, attributes, and link count. An open
read handle excludes concurrent write and delete sharing. Every snapshot rejects
directories, devices, reparse points, pending deletion, and multiple hard links.
The POSIX path continues to compare its native `lstat` and `fstat` results.
[Windows handle metadata](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getfileinformationbyhandleex),
[file identity](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_id_info),
[file sharing](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)

The integration cases exercise the installed comparison command against rewritten
files, linked inputs, directories, and an oversized measurement. They run through
the existing Windows compatibility and merge queue workflows. No local tests or
licensed CAD applications were executed for this repair.
