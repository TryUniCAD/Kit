# Hidden sketches can drive active features

A native FCStd sketch can store `Visibility=false` and still supply the profile of an active Pad.
FreeCAD visibility controls whether the object appears in the 3D view.
[FreeCAD visibility command](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Std_ToggleVisibility.md?plain=1)

Keep the native visibility property when reading or updating a sketch.
Read explicit sketch suppression from `SourceSuppressed` or `Suppressed` and use the resulting state when interpreting feature dependencies.
The two disclosed profiles in the [FCStd replay](../../../../re/solidworks/measurements/2026/FreecadSketchVisibility01.json) each retain the native hidden flag, active Pad link and all 17 parameters.
