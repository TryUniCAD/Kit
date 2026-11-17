# A fixed centre leaves the circle radius editable

The fixed logical type `0x11` does not identify which geometry it fixes. In the ordinary 2026 pocket, its owned `sgPointHandle` resolves to the arc's centre slot. The two endpoints instead refer to the shared seam slot. Setting the entire circle's `fixed` flag would attach solver intent to the radius as well as the centre.

Follow the typed point handle to its local point array slot and check that the circular arc uses it as its distinct centre. Emit a fixed relation on the circle's `center` subelement and preserve the separate driving radius. [Archive ownership evidence](../../../../../re/solidworks/records/PocketCenterReadback2026.md) · [SDK change](../../../../Changes/Solidworks/Inspection/Sketches/SolidworksPocketCenterFixation.md)
