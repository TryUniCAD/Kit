# The final sketch edge has its own width

A sketch's line-style marker continues to the next matching style marker or the end of the enclosing feature span. Inside an ordinary 2026 four-line rectangle the first three marker distances can match the line record width. The last marker also covers the following arrays and feature fields. In the generated blind-pocket rectangle it spanned 575 bytes even though the actual line row was still 92 bytes, with endpoint slots `3,0`.

When the typed point and line arrays and empty arc count establish ownership, use the row's own layout to read its endpoints. Verify the closed cycle and corner coordinates before emitting a rectangle. [Sketch array proof](../../../../../re/solidworks/records/RectangleSketchOwners2026.md) · [Generated pocket reader change](../../../../Changes/Solidworks/Inspection/Sketches/SolidworksPocketSketchReadback.md).
