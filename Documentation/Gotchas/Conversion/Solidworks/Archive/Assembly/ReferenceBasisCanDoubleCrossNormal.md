# A reference frame can recompute its third axis

A byte comparison between two independent frame models can fail even when both
represent the same rigid placement. The SDK frame retains the normalized third
basis vector calculated before it reconstructs the second tangent. The older
research `PlaneFrame.normal` property crosses the final two tangents again.

For the disclosed synthetic rotation of -29 degrees about Z, the latter path
produced `1.0000000000000002` for the third diagonal word while the retained
normalized basis produced `1.0`. The extra arithmetic propagated into bounds,
plane caches and MatesList. It was not an endpoint ownership or driving-value
disagreement. The authored principal-Z API matrix has third basis `(0,0,1)`.

Keep the exact arithmetic convention explicit in independent reconstruction
adapters. `SdkReferenceFrame` retains the normalized basis and is used only by
the independent research counterpart, including its placed-datum frame input.
The product writer and the failed comparison records remain unchanged. No
captured numeric word is substituted into either generated graph.

[Construction and sealed-evaluation protocol](../../../../../../re/solidworks/records/SdkOriginalPlanarMateEvaluation2026.md)
