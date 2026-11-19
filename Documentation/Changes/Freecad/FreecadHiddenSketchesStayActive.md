# FreeCAD hidden sketches stay active

The native FCStd reader preserves hidden sketches as active profile drivers when the source has no explicit suppression.
A boolean `SourceSuppressed` property takes precedence over `Suppressed`.
Kit writes explicit suppression edits to the native sketch record and retains the source visibility property.

Kit can restore an unchanged archive carried by an older version that interpreted visibility as suppression.
The carried model and an independent parse of the archive must both match the stored semantic digest.
The compatibility check follows the normal archive validation and external reference limits.
For an edited older carrier, the verified archive supplies the actual suppression state for unchanged inherited flags.

The integration cases cover suppression priority, driving diameter edits, and exact restoration of old carriers and linked profiles. [Integration cases](../../../tests/Convert/Freecad/FreecadTests.py)

The initial reader correction was measured on 171 path reads, with 318 sketch states corrected in 94 paths.
The earlier research run reported 144 integration passes and 10 skips and records the tested adapter hashes. [Initial replay](../../../re/solidworks/measurements/2026/FreecadSketchVisibility01.json)

[Adapter guide](../../Reference/Adapters/Freecad.md), [visibility gotcha](../../Gotchas/Conversion/Freecad/HiddenSketchesCanDriveActiveFeatures.md), and [legacy replay digest gotcha](../../Gotchas/Conversion/Freecad/LegacySketchReplayDigests.md)
