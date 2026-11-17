# Native Parasolid fin vertex is the endpoint

In the current 2026 rectangle partitions, a fin's `vertex` is the endpoint
of its directed traversal. Its mate's `vertex` is the start. The forward
links connect endpoint to start across all 24 directed edge uses in each
of the six disclosed rectangles. Those raw loops wind outward and agree
with the corresponding plane and face senses.

The SDK projection of the same files yields inward loop order even though
the corners and planes match. When checking a current-format cache against
the native winding, follow `HALFEDGE.forward` and compare both ends using
the mate and vertex fields. The signed-volume check then agrees with the
native shell orientation.
[Typed wire and SDK comparison](../../../../../../re/solidworks/records/PopulatedPrismPartition2026.md#topology-and-ownership)
