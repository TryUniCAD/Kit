# A native circle can expose a separate fixed centre entity

Portable authoring can express a centre fixation with the circle's
`center` subelement. On the measured cache-free circle outputs, strict
SOLIDWORKS readback exposes the circle and its native centre as two distinct
sketch entities with separate permanent marks. The fixed relation targets the
centre point. The radius or diameter relation and the closed profile target
the circle.

Treat the point as a linked sketch entity when inspecting the recovered
document. Fresh authoring and native readback have different ownership
shapes. Re-publication needs a specific centre-and-driver projection and a
full comparison against the regenerated source document. Removing the point
from the readback alone loses its owned relation. Also check the
[binary64 centre projection rule](CircleCentreProjectionsCanRoundDifferently.md).
[Six disclosed readbacks](../../../../../../re/solidworks/records/AggregateCircleEndPort2026.md)
