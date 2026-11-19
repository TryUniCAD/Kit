# Sheet property decimals can round native doubles

The public layout reader obtains paper dimensions from decimal property text. The actual typed sheet owns binary doubles. These representations can differ by one floating-point unit even for the same ordinary paper.

The second private portable reconstruction failed the unchanged blank-sheet constructor's exact paper check. Public height was `0.2159 m`; actual `moDrSheet.f3e8` and the existing constructor both contained `8.5 * 0.0254`, or `0.21589999999999998 m`. Active-sheet identity, width and view content were not the mismatch. The shared property writer formats paper values with six digits after the decimal point, and the layout reader converts that text with `float`.

Use the actual typed sheet dimensions as source geometry and check the property-derived values independently. The ordinary public blank writer and its constructor now share a one-ULP check for the same physical ANSI A dimensions. The matching layout-index decimal converts to the canonical native paper values. Other paper dimensions fail admission. [Public blank writer](../../../../../Changes/Solidworks/Construction/SolidworksPublicBlankDrawingWriter.md)

The guarded public integration checks both input representations against the actual sheet values through the normal writer and layout reader.
