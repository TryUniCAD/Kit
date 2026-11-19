# FreeCAD hidden sketches stay active

The native FCStd reader preserves hidden sketches as active profile drivers when the source has no explicit suppression.
`SourceSuppressed` takes precedence over `Suppressed` when both properties exist.
When an archive edit rebuilds a native sketch record, Kit preserves the existing `Visibility` property.
These behaviors apply on the ordinary strict read and write paths.

The integration case exercises hidden active profiles and both explicit suppression properties through an adapter read, parameter edit and archive write. [Integration case](../../../tests/Convert/Freecad/FreecadTests.py)

A prior replay on the same adapter source files read 171 available paths and corrected 318 sketch states in 94 paths.
The report records 144 integration passes and 10 skips from that research run. [FCStd replay](../../../re/solidworks/measurements/2026/FreecadSketchVisibility01.json)

[Adapter guide](../../Reference/Adapters/Freecad.md) and [native property gotcha](../../Gotchas/Conversion/Freecad/HiddenSketchesCanDriveActiveFeatures.md)
