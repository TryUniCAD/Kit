# Record the native process exit status

The retained SOLIDWORKS observer now keeps a query handle to its exact COM server process.
It records the process exit code before controller cleanup can close the application.
The report includes the numeric code, hexadecimal code, and whether the process remains active.
Code `259` means the process remains active when queried.
The [Windows process status API](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getexitcodeprocess) defines this result.
A lost COM connection or terminated process alone does not identify a native fault.

The existing `PrepareSolidworks.py` entry point enables this record automatically.
The handle is closed on every exit path, including failed observation setup.
Controller cleanup still runs if the exit-status query fails.
This is an observation tool, not a writer dependency or acceptance result.
Static syntax inspection passed. Native results remain pending.

The full native profile also records the body collection output count after each call.
The count belongs to the output array at offset `+0x10`, as used by the native finalization loop.
Raw return-register values remain separately labeled and are not treated as body counts.
