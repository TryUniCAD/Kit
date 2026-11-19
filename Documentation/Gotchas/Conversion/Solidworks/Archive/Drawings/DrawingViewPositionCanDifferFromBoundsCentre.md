# Drawing view position can differ from the bounds centre

The Header2 rectangle centre and the authored view position coincide for the measured centred rectangular controls. That equality can fail when a corner-anchored child changes and the view is moved.

In six edited SOLIDWORKS 2026 SP05.2 states, `moAbsoluteView.f778` and the native API both gave `(0.121541, 0.090241)` m. The Header2 bounding box centre was `(0.1239623695, 0.090241)` m. The two archive owners still agreed on all four outline coordinates.

Read the planar position from Definition. Corroborate the separate outline against Header2. [Edited view readback](../../../../../../re/solidworks/measurements/2026/DrawingEditedViewPosition01.json)
