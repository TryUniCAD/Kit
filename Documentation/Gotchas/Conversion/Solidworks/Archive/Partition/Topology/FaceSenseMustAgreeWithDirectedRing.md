# Face sense must agree with the directed ring

On the witnessed current SOLIDWORKS attributed active partition, each plane
carrier has positive sense. The face sense matches the sign of the directed
fin ring normal dotted with the plane normal. Each fin stores its terminal
vertex, so forward traversal retains the ring direction.

Flipping one face sense can change the projected face orientation while
leaving the closed ring, shell incidence and signed volume unchanged. Check
the stored face sense against the proven ring direction and plane carrier
before projecting the face. The attributed reader refuses a negative plane
carrier until that convention is independently established.

[Current fin traversal](../NativeParasolidFinVertexIsTheEnd.md) ·
[Maintained attributed partition checks](../../../../../../../re/tooling/sw2026/attributed_read/CheckAttributedFaults.py)
