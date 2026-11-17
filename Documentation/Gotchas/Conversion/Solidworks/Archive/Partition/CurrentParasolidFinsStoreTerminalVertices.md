# Current Parasolid fins store terminal vertices

For the measured current 2026 rectangular partitions, a loop follows each
fin's forward link and crosses each directed edge from its mate's vertex
to its own vertex. The six boundary loops have outward orientation.

The SDK `GetEdgeUseMut` starts at the fin's own vertex, and `WalkCoedgeRing`
follows the backward link in the current-schema branch. The two choices
produce closed inward loops in L1, A13, A14 and the generated attached
rectangle. Point locations, the absolute volume, surface area and centroid
still agree. A typed forward traversal is necessary when checking signed
volume or outward winding in this cohort.

[Generated and native comparison](../../../../../../re/solidworks/records/GeneratedRectanglePartition2026.md#standalone-archive-attachment)
