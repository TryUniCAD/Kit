# Mid-plane stock bounds in parametric reads

Reading a supported part with geometry disabled now uses both half-depths of a typed mid-plane stock extrusion. The stock profile's actual support origin and normal define the two bounding stations. The geometry-disabled option continues to return the portable feature history and its body summary.

The before-and-after check uses three disclosed Front, Top and Right parts with a mid-plane rectangle and an interior circular through-all cut. All six corrected path and bytes reads match the vertex bounds of the separately decoded active solid. [Process receipt](../../../../../re/solidworks/measurements/2026/MidPlaneStockBounds01.json) [Bounds gotcha](../../../../Gotchas/Conversion/Solidworks/Model/Extrusion/MidPlaneBoundsUseBothHalfDepths.md)
