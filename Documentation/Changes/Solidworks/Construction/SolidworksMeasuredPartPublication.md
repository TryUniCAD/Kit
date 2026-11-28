# Require exact native evidence for SOLIDWORKS part output

The SDK can regenerate an exact measured cold part after a strict SDK read.
It uses the linked Front-plane line loop and the actual driving D1. The final
locator supplies the expected part name. Before publication, Kit compares
the complete strict readback against an in-memory projection of its newly
generated archive, including the default scaffold, B-rep, and provenance.
A changed source hash, extra metadata, or changed topology refuses publication.
This path applies to exact cold readbacks with a matching offline receipt.

The authored scope has one unconstrained closed loop of three to sixty-four
straight segments and one driving boss depth. The archive retains every
modeled segment and the actual depth parameter. Sketch dimensions and
relations require their own profile, and a request containing them refuses
before output staging.

Public SOLIDWORKS part writes release a file or write to a binary stream only
when the complete regenerated archive matches a passing offline native
measurement from SOLIDWORKS 2026 SP05.2. Direct adapter calls and ordinary
registry paths use the same gate. A missing or mismatched receipt protects
both existing files and caller-owned streams. Measured binary streams must
be writable, seekable and empty with the cursor at position zero.

For SDK use, supply a plain dictionary as
`values["solidworks_native_measurement"]` in `write_document` or
`WriteOptions`. Its `written_at` specifies the original measured creation
epoch in whole Unix seconds. Its `receipt` contains a parsed
[standalone part evidence report](../../../../re/solidworks/measurements/2026/SdkDefaultPartNative01.json).
For CLI use, store the same dictionary as JSON and pass
`--native-measurement Measurement.json`. Receipt paths can begin with `~/`.
The previous candidate option is removed.

Use the [research preparation command](../../../../re/tooling/sw2026/PreparePlainPartEvidence.py)
with authored neutral JSON, its intended absolute Windows locator, the
creation epoch and a fresh scratch directory. The command generates the
complete candidate and records its file and stream digests under
`awaiting_native_measurement`. Use that file in a separate controlled
SOLIDWORKS measurement. The command returns a candidate digest and manifest
digest for custody. Publication still uses the normal SDK or CLI.

Kit authenticates both published native reports by their canonical JSON
digests. The receipt must bind the complete regenerated archive, exact
oracle build and measured lifecycle. A successful match reports both native
acceptance flags. The writer uses the caller's parsed receipt in memory.
Use the original report for the Python compression runtime that produced
the archive.
[Classic zlib evidence](../../../../re/solidworks/measurements/2026/SdkDefaultPartNative01.json)
[Zlib-ng evidence](../../../../re/solidworks/measurements/2026/SdkDefaultPartZlibNgNative01.json)

The [disclosed follow-up](../../../../re/solidworks/records/MeasuredPartPublication2026.md)
reused both actual passing offline measurements. It reproduced the complete
native-tested archives through staged paths, strict streams, direct streams
and the CLI. Tampered and missing evidence preserved the destinations.


The [standalone stream follow-up](../../../../re/solidworks/measurements/2026/SdkMeasuredStandaloneStream01.json)
verified both native-tested archives through empty memory and write-only
file streams. Both entry points preserved bytes and cursor on incompatible
destinations. Generic JSON append and literal home-relative CLI receipts
also passed.
