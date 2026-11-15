# Versioned activation can return a user-owned session

## Expectation

`DispatchEx("SldWorks.Application.34")` creates a separate process that an oracle
controller may configure and close. An application absent from the active-object
table, or with visibility false, has no user work to preserve.

## Actual behavior

The exact 2026 probe returned the same process ID that existed before activation.
Its executable version, hash and x64 architecture matched the selected oracle.
No application property was written and no document API was called by the probe.
The preexisting process remained running afterward.

A subsequent read-only inspection selected that exact process ID before reading
document metadata. It found two open documents, including one unsaved modified
drawing, with visibility false and user-control true. The earlier active-object
lookup had been unavailable. Neither observation grants process ownership or
permission to close its documents.

The [controlled evidence](../../../../../re/solidworks/measurements/2026/OracleInstanceReuse.json)
records the source revisions, tool hashes, native identity and process sets.
User document titles and paths are omitted from that public record. No geometry
or saved streams were inspected, and the session was not closed.

## Workaround

Check the returned process ID against the pre-activation process set before
changing application properties, using document APIs or issuing an exit command.
Treat a matching preexisting PID as unowned unless actual task ownership or a
user handoff establishes otherwise. An unavailable active-object registration
and an invisible window do not establish an empty session. Preserve unsaved
work and wait for the owner before restarting that shared oracle.
