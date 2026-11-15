# Existing SOLIDWORKS session inventory

The [existing-session inspector](../../../../../re/tooling/sw2026/InspectExistingSession.py) queries an explicitly selected running SOLIDWORKS 2026 process.
It attaches only through `GetActiveObject(Swapp.PROGID)`, using the versioned `.34` program identifier.
It does not activate a new instance, set application properties, dismiss dialogs, or open, save, rebuild, or close documents.
It issues no application exit, process termination, or licensing command.
Existing applications, license servers, and their services remain outside its control.

Stage the inspector with the matching committed `Swapp.py` and `OracleIdentity.py`.
Use an absolute unused output file whose parent directory already exists:

```text
python InspectExistingSession.py --expected-pid <existing-pid> --expected-sha256 <pinned-executable-sha256> --output <absolute-unused-report.json>
```

The PID and executable SHA-256 are required.
The [identity helper](../../../../../re/tooling/sw2026/OracleIdentity.py) supplies the pinned four-word executable version.
The inspector verifies the active object's PID before any document query.
It then checks native executable name, exact version, and hash.
An unavailable active object or an identity mismatch fails explicitly, without an activation fallback.

The report records script and sidecar hashes, application PIDs before and after, and native identity before and after document inventory.
Native identity includes process creation time, allowing the owner to detect a reused PID.
Two snapshots collect `GetDocumentCount`, `GetDocuments`, document title, path, and dirty status.
Each snapshot checks counts before and after traversal.
The snapshots compare title/path/dirty multisets, retaining duplicate rows while allowing enumeration order to vary.
Identity and application PID inventories must also remain stable.

The report is checkpointed before every potentially blocking COM operation.
A host supervisor can read the current stage if a call stalls.
The tool does not impose a COM timeout or perform timeout cleanup on another process.
Its final cleanup releases COM references and uninitializes COM only.
The [host-timeout finding](../../../../Gotchas/Conversion/Solidworks/Tracing/GuestTimeoutsDoNotBoundHostTransport.md) explains why supervision remains external.
The [existing-session finding](../../../../Gotchas/Conversion/Solidworks/Tracing/VersionedComActivationCanReuseUserSession.md) explains the ownership boundary.

A successful exit establishes only a completed, stable health inventory for that observation interval.
The snapshots are not an atomic document transaction.
They do not establish license recovery, source correctness, or native CAD-file acceptance.
Verification of this addition is limited to AST and static source inspection; it has not yet run against a live session.
No local tests or CAD application calls were executed during preparation.
