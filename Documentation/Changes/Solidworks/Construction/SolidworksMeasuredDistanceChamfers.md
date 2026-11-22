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
drivers, actual predecessor, two physical selections and analytic solid.
Both writers can regenerate a complete strict cold readback when the
model, original measured locator and receipt still agree. The regenerated
archive must reproduce the complete observed document before publication.
Both entry points report the same native capability transfers.

Strict inspection refuses unqualified SOLIDWORKS 2026 chamfer history,
including saved states requested without geometry. Permissive inspection
keeps an unresolved-history warning and a native-only feature record.
This applies when the native class or the explicit Chamfer keyword
identifies the feature without a decoded operation. Raw Parasolid
extraction remains available for readable saved payloads. The shared
integration suite uses a hash-pinned native save for both inspection modes
and both raw payloads.

The [release proof](../../../../re/solidworks/records/ChamferDistanceMain2026.md)
links the native measurements and the guarded main-line read and write
checks. Both original candidates reproduce all ten streams. Each private
changed-driver comparison changes the recovered solid and fails public
publication with the old receipt.
