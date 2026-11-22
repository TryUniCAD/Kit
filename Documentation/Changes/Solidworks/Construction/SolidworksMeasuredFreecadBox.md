# Measured FreeCAD box conversion to SOLIDWORKS

Kit can convert the disclosed FreeCAD 0.21.2 F14c attached box to its measured
SOLIDWORKS 2026 SP05.2 part. The output has one reversed blind boss, three
independent driving dimensions and the three signed principal axes. Each axis
selects its actual ordered plane parents. Strict reading recovers the named
solid, support, origin coincidence, dimensions and complete axis selections.
The design-only reading mode preserves these owners through neutral JSON.

Pass the exact Trial02 measurement in the existing
`solidworks_native_measurement` write option. Supply the matching epoch and the
original UTF-8 summary and terminal texts as `receipt.summary` and
`receipt.native_result`. On Windows the file destination must be the measured
absolute path. An empty standalone stream needs that exact `final_destination`.
The CLI reads the same envelope through `--native-measurement`.

The report includes native transfer of six functional capabilities and a
separate source evidence record for the FreeCAD archive, shape encodings and
provenance. The output cannot reproduce the original FreeCAD archive bytes.
Publication requires the exact intact source, authenticated receipts and the
complete measured output hash. Other FreeCAD parts, native-saved SOLIDWORKS
derivatives and other output paths require separate qualification.

Trial02 passed two controls, four native process lifetimes and 528 checks.
The main-based worker proof reproduces the measured 10,707-byte file through the
ordinary stream APIs and preserves the two earlier plain-part results.
The main-based Windows SDK and CLI also published the same exact bytes to
the measured path with explicit and inferred target formats.
[Native summary](../../../../re/solidworks/measurements/2026/AttachedBoxAxesNative01.json)
[Verification and scope](../../../../re/solidworks/records/MeasuredFreecadBoxMain2026.md)
[Windows file publication](../../../../re/solidworks/measurements/2026/AttachedBoxAxesMainWindowsPublication01.json)
