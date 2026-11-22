# Measured SOLIDWORKS distance chamfers

The SOLIDWORKS 2026 SP05.2 part writer accepts a neutral millimetre document
with one forward rectangular Front-plane blind boss and one edge chamfer.
Equal distance owns one driving length `D1`. Two distances own ordered,
independent lengths `D1` and `D3` and two actual signed incident sides.

Both SDK stream entry points use the existing
`values["solidworks_native_measurement"]` option. The
[adapter guide](../../../Reference/Adapters/Solidworks.md#measured-distance-chamfers)
describes the exact receipt, locator and output conditions. The writer
regenerates the complete archive from its neutral model. It publishes when
the complete bytes match the measured lifecycle and leaves refused output
streams untouched.

Strict inspection of the supported cold archive recovers the editable
drivers, actual predecessor and selections, and the analytic chamfer solid.
The publication scope is original neutral input. A geometry-only or saved
chamfer has a different source contract.

The [release proof](../../../../re/solidworks/records/ChamferDistanceMain2026.md)
links the native measurements and the guarded main-line read and write
checks. Both original candidates reproduce all ten streams. Each private
changed-driver comparison changes the recovered solid and fails public
publication with the old receipt.
