# Cylinder ring vertices are reader-derived

The public B-rep for a closed cylinder exposes a seam vertex on each circular edge. Six saved SOLIDWORKS 2026 cylinder states carry zero corresponding vertex and point records in their active partitions. Each ring consists of a circular edge with two opposite self-linked fins. Each cap owns one such loop, and the lateral face owns both.

Build the saved ring from the actual periodic circle and its two fins. Derive seam vertices at the neutral B-rep boundary. Use the face's persistent kernel `node_id` for the selected mate endpoint and preserve its independent sketch and atom ownership.

[Disclosed topology and guarded generation checks](../../../../../../re/solidworks/records/CylinderPartitionConstruction2026.md)
