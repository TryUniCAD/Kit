# SOLIDWORKS scaled named drawing views

The opt-in SOLIDWORKS 2026 drawing reader exposes a single external part view with Front, Top, Right or Isometric orientation and an explicit positive scale. Use `open_document(source, strict=False)` and read the view's `orientation_name`, `scale_ratio`, `position` and `model_to_sheet` from its sheet. The affine transform operates on metres. The neutral JSON format carries the same layout and model reference.

Four disclosed native sources retain complete byte identity for Definition and Header2. The SDK recovers the four non-unit ratios and validates 36 geometric probes at the part bounding-box vertices and centre. All four layout records survive neutral JSON round trips. The sources pass native authoring and fresh reopen across ten controlled processes. [Receipt](../../../../../../re/solidworks/measurements/2026/DrawingScaledViewSdkRead01.json) [Native transform rules](../../../../../../re/solidworks/records/DrawingScaledViewProjection2026.md)

This remains layout inspection for one unformatted sheet. Strict reads and production writing stay outside this change. [Rotated basis gotcha](../../../../../Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingRotationsNeedTheMatrixMethod.md)
