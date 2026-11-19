# FreeCAD hidden sketches stay active

The native FCStd reader preserves hidden sketches as active profile drivers when the source has no explicit suppression.
`SourceSuppressed` and `Suppressed` still control sketch suppression, and native archive edits preserve the existing `Visibility` property.
The fix applies on the ordinary strict read path and needs no adapter option.

The [integration suite](../../../tests/Convert/Freecad/FreecadTests.py) exercises hidden active profiles and both explicit suppression properties through read, edit and archive write.
The combined FreeCAD integration run passed 144 tests with ten skips for unavailable bundled examples.
In the [FCStd replay](../../../re/solidworks/measurements/2026/FreecadSketchVisibility01.json), all 171 available paths read strictly.
The correction changes 318 sketch states in 94 paths, with associated derived digest updates and zero other field differences.

SOLIDWORKS conversion of these original FCStd documents remains open under the [corpus coverage register](../../../re/solidworks/CorpusCoverage.md).
[Adapter guide](../../Reference/Adapters/Freecad.md) and [native property gotcha](../../Gotchas/Conversion/Freecad/HiddenSketchesCanDriveActiveFeatures.md)
