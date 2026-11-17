# Forward edge anchors in generated rectangle partitions

The SOLIDWORKS 2026 rectangle research writer now binds each edge to its
coedge in the authored direction. The kernel uses that coedge to return
the edge endpoints in order.

The paired probe regenerates the part from its original neutral dimensions.
It changes five edge-to-fin pointers and reproduces every other active
field, all other logical streams, and the stored rollback section. Native
open and rebuild observations on the corrected part are pending.

[Rule, reproduction and comparison](../../../../../re/solidworks/records/RectangleEdgeAnchor2026.md)
