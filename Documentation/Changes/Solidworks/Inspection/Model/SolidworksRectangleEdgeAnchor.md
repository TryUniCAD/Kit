# Forward edge anchors in generated rectangle partitions

The SOLIDWORKS 2026 rectangle research writer now binds each edge to its
coedge in the authored direction. The kernel uses that coedge to return
the edge endpoints in order.

The paired probe regenerates the part from its original neutral dimensions.
It changes five edge-to-fin pointers and reproduces every other active
field, all other logical streams, and the stored rollback section. Both
native opens returned warning 32 and zero solids. Explicit rebuild restored
an extrusion-owned solid with the expected volume, area and centre in each
case. Both L1 controls passed. The cache still fails the native open gate.

[Rule, reproduction and comparison](../../../../../re/solidworks/records/RectangleEdgeAnchor2026.md)
