# Oracle timeout cleanup needs process creation identity

## Expectation

A worker report contains an oracle PID, executable hash and version.
Those recorded values could appear sufficient for later timeout cleanup.

## Observed behavior

The earlier parent cleanup passed the recorded PID to process-tree termination after the worker ended.
It did not retain the worker's process handle or compare a current creation time.
Microsoft documents that [process IDs can be reused](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/ns-processthreadsapi-process_information)
after process objects are freed.
An old report therefore does not identify the current owner of that PID.
This defect was found by source inspection, not an observed termination of an unrelated process.

## Workaround

Record the exact creation `FILETIME` while the worker owns the application.
Open a process handle with query, synchronization and termination rights for parent cleanup.
Compare its current creation time with the worker's recorded identity.
Refuse cleanup when the identity is missing or different.
Terminate and wait through that matching handle.
Do not expand the action to an unverified process tree.

The [oracle ownership change](../../../../Changes/Solidworks/Inspection/SolidworksOracleSessionOwnership.md)
implements this boundary and records its verification limits.
