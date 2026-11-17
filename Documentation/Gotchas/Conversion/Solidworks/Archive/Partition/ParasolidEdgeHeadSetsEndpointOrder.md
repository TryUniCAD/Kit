# A Parasolid edge head sets the endpoint order

An undirected edge with two reciprocal fins can form valid closed loops
with either fin as its anchor. On the current SOLIDWORKS 2026 rectangular
partition layout, the edge endpoint query starts at the anchor's mate
vertex and ends at its own terminal vertex. Choosing the opposite
anchor reverses the edge's endpoint order while the face loops stay closed.

Assign the anchor from the directed edge and its actual coedges. In the
ordinary generated straight prism, select the coedge that follows the
edge's authored start and end. Check the endpoints against the supporting
line as well as the perimeter.

[Kernel trace and controlled comparison](../../../../../../re/solidworks/records/RectangleEdgeAnchor2026.md)
