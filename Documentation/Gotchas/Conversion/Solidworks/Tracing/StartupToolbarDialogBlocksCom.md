# A toolbar startup dialog can block COM activation

## Expectation

The versioned COM call returns the fresh SOLIDWORKS process before the oracle opens a control file.

## Observed behavior

On SOLIDWORKS 2026 SP05.2, the application created a process in the current Windows session.
It displayed a toolbar consistency dialog about four seconds after activation began.
The dialog said that SOLIDWORKS would use the default toolbar setting.

The versioned COM call returned `0x80080005` after about 120 seconds.
Windows recorded DistributedCOM event 10010 for the registered SOLIDWORKS class.
The original control remained unchanged and the session opened no CAD files.
Read-only window inspection identified the dialog. [Startup receipt](../../../../../re/solidworks/measurements/2026/OracleComToolbarStartup01.json)

## Workaround

Check for a visible startup dialog on the new process if versioned COM activation times out.
Resolve the toolbar prompt with the Windows profile owner before starting another native bracket.
Require a fresh passing control before measuring candidates. [Session ownership](VersionedComActivationCanReuseUserSession.md)
