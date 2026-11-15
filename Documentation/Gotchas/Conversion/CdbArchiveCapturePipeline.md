# CDB archive capture pipeline

## Expectation

The five-line archive recipe can start a new SOLIDWORKS process with a triangle part, reload `swccu.dll` at startup, and obtain the same native object trace without adaptation.

## Actual behavior

At the initial process breakpoint, `swccu.dll` has not loaded. `.reload /f swccu.dll` reports that the file cannot be found and leaves a spurious `.dll` command before `Command file execution failed`, so no object events are captured.

Changing only the breakpoints to deferred `bu swccu+offset` addresses fixes their binding, but a debugger-launched application still does not necessarily load the requested document. That path also produced zero object events, independently of document validity.

The successful recipe is to use the deferred addresses and attach to the live SOLIDWORKS process, then have the oracle open the document through its API. The triangle attached trace completed with `ORACLE_EXIT=0`, 300 object reads, and 300 class reads. Segmentation tiled all 10,601 bytes with 40 class definitions and no counter mismatches.

## Workaround

Use deferred module-plus-offset breakpoints, retain `0x6d` as the stream-identity guard for this family, and drive the document open through `OracleLoadDiagnostics.exe`. Do not infer a native file defect from a failed `.reload`, a debugger command-file error, or a launch that never consumes the document.

Refresh the SOLIDWORKS process identity immediately before attaching. A process id that was valid for earlier checks can later be stale: the primitive capture that targeted `10200` failed with `Cannot debug pid 10200, Win32 error 0n87`, while the live process reported a different id. Capture the current id through the VM process list and do not convert this failure into a file-format diagnosis.

Check the oracle exit code, trace event identities, nesting, and byte tiling before trusting any recovered records. An unused debugger diagnostic after those checks does not turn a failed capture into valid evidence; the successful run must be distinguishable from the earlier zero-event attempts.

See [the triangle research status](../../re/solidworks/records/PolylineThreePad.md), [archive buffer guards](SolidworksArchiveBufferGuards.md), and [isolated oracle share paths](OracleWorktreeSharePaths.md).
