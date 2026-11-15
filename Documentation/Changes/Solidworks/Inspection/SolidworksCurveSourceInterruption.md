# Interrupted curve-source control reopening

The [sanitized source-preflight record](../../../../re/solidworks/measurements/2026/CurveSourcePreflight07Interrupted.json)
publishes the incomplete annulus/capsule preflight on committed author source
`4ed467bc94a9e7da00bc9782a603a525250242cd`.
One rectangle-control authoring phase passed seven numeric checks, with one solid
body and 25 feature entries without errors or warnings.
Fresh reopening of that control stopped producing records at `OpenDoc6`.
Neither candidate was measured, and no healthy trailing control or family lock
was obtained. The preflight is invalid for acceptance.

The publication retains source, tool, executable and raw-record hashes, process
lifetime identities, completed control measurements and the last incomplete API
call. A missing return or timeout result does not establish a format defect or
application crash. Native files, private paths, the VM screenshot and proprietary
software are not included.

The oracle owner confirmed a VM reset after the pause operation failed.
A later current-user Windows version command and process inventory completed.
That recovery established command execution, not COM readiness or native CAD
health. The [timeout gotcha](../../../Gotchas/Conversion/Solidworks/Tracing/GuestTimeoutsDoNotBoundHostTransport.md)
and [host supervisor](SolidworksOracleHostDeadline.md) describe the separate
supervision boundary for subsequent runs.

Use the record to audit this interrupted attempt. Do not resume its directory or
count its author-only control phase as candidate acceptance. Start fresh source
measurements between healthy controls before creating a family lock.
The [SOLIDWORKS adapter guide](../../../Reference/Adapters/Solidworks.md) continues
to describe read-only production support.

Verification independently rechecked all six published raw JSON hashes and the
seven completed numeric checks. Publication used metadata only, with no native
file interpretation, local product tests or additional CAD execution.
