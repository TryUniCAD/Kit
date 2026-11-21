# Drawing view bounds use the view centre and extents

For an ordinary front view of a rectangular prism, model-to-view translation places the model centre at the authored view position. SOLIDWORKS stores the projected view rectangle from that position plus or minus the child half extents. Applying the transform to each source bound introduces a one-bit rounding difference in some coordinates. Use the view position and half extents to reproduce the two measured rectangles exactly, then apply the paper-dependent outline margin. [Projection rule and evidence](../../../../../../re/solidworks/records/DrawingFrontViewConstruction2026.md#projection-values)

The construction rule applies to the measured centred view. The saved position of an edited asymmetric view has its own Definition field. [Edited view position and bounds](DrawingViewPositionCanDifferFromBoundsCentre.md)
