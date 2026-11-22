# Require exact native evidence for SOLIDWORKS part output

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
The previous candidate option is removed. Controlled measurements can still generate a candidate through the
internal in-memory preparation path.

The caller establishes the authenticity of the unsigned oracle report.
The writer verifies its required structure, oracle build and digest binding
without reading a report or running CAD. A successful match reports both
native acceptance flags. The output must retain the measured encoded locator.

The [disclosed follow-up](../../../../re/solidworks/records/MeasuredPartPublication2026.md)
reused both actual passing offline measurements. It reproduced the complete
native-tested archives through staged paths, strict streams, direct streams
and the CLI. Tampered and missing evidence preserved the destinations.


The [standalone stream follow-up](../../../../re/solidworks/measurements/2026/SdkMeasuredStandaloneStream01.json)
verified both native-tested archives through empty memory and write-only
file streams. Both entry points preserved bytes and cursor on incompatible
destinations. Generic JSON append and literal home-relative CLI receipts
also passed.
