# Fusion parameter values use database units

`Parameter.unit` describes the display unit.
It does not describe the numeric value returned by `Parameter.value`.
Lengths use centimetres and angles use radians in the Fusion API, including when the display unit is millimetres or degrees.

Multiplying a numeric value by its display-unit factor produces a wrong verification measurement.
The native collector now records the internal numeric unit separately from `display_unit`.
The comparator normalizes internal centimetres to millimetres and retains radians.

The serialized P03 compatibility case compares 40 millimetres against the native-style value of 4 centimetres.
No licensed Fusion execution was available during implementation.

See the Autodesk [Parameter reference](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Parameter.htm) and [SketchLinearDimension reference](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_SketchLinearDimension.htm).
