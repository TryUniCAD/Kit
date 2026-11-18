# Centered contours keep their own frontier

For a plain polygon, the body-contour frontier and next line-array ID initially coincide. That does not make them the same owner. A centered rectangle appends two construction diagonals without making them body edges.

The qualified construction preserves the original contour frontier `sgSketch.f130`, advances `f56c` and the line-creation counter from the actual full line array, and advances the point counter from the actual point rows. It preserves the contour's existing two endpoint handles while deriving total incident-line counts. Deriving every frontier from the final line-array length would put construction geometry into the contour's bookkeeping.

The SDK port keeps the four-line body contour in `ProfileGraph.GeometryValue` and retains the actual appended center/reference geometry in the returned `CenterGraph` and native sketch arrays. Independent mathematical stream comparison and fresh typed preparation verify both structures. Fresh native SDK lifecycle remains a separate gate.

[Construction and evidence](../../../../../../re/solidworks/records/SdkCenteredRectangleConstruction2026.md) · [Process receipt](../../../../../../re/solidworks/measurements/2026/SdkOriginCenteredConstruction01.json)
