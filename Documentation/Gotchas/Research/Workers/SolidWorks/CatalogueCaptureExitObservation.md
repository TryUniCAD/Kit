# A completed catalogue capture save can precede a shutdown timeout

The first native phase must complete its save, close its documents and exit
before the catalogue starts a fresh process for reopen. A successful `ExitApp`
call records the request. The launch handle supplies the separate exit evidence.

On SOLIDWORKS 34.4.1.1011, the 24 November 2026 discovery run at source
`866a518574b3ef34e887b5bec91aa37dc67d864a` saved a single-body P04 model on
all 21 failed attempts with zero save errors or warnings. The native receipt
recorded the exit request with no COM cleanup exceptions. The owner receipt
reported that normal exit was unobserved, and the fresh reopen never ran. Two
cases passed on later attempts; six exhausted three attempts. A separate
three-case written-recipe batch reached its phase deadline after the first save.
Its last saved report did not locate the blocked call.

At `95afdb67740e377cc33882f12fb3e5a90d2558d1`, an owned boss-extrude control
also timed out after saving and requesting exit. Read-only Windows observation
found a responding main window on the exact owned PID before the timeout.
After the empty-document check and successful COM exit request, the launcher
can ask the verified process's main window to close within the original
deadline. A posted close request requires separate process exit evidence.
[Windows normal window close](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.process.closemainwindow?view=netframework-4.8)

The verified SOLIDWORKS frame alone left the 28 mm cut-extrude process alive.
The replay at `8802a83fb0c8503cc7e979f977037af7d89ba015` used `QuitDoc` to
close the sole read-only stock control in program-owned background mode. The
guarded frame request then finished both phases with observed normal exits.
Require the process receipts and independent reopen before using this result.
[SOLIDWORKS last-document close](https://help.solidworks.com/2021/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.ISldWorks~QuitDoc.html)

Keep `first-native.json`, `first-owner.json`, and `first.stderr.log` together
under `NativeAttempts` when diagnosing shutdown. Use a fresh directory to
compare a revised worker, and retain the independent reopen and exit checks.
The owner thread can drain unused COM wrappers in its own apartment.
[Microsoft COM wrapper cleanup](https://learn.microsoft.com/en-us/dotnet/api/system.runtime.interopservices.marshal.cleanupunusedobjectscurrentcontext)
