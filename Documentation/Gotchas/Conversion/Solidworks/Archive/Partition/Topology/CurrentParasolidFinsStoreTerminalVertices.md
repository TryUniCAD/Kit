# Current Parasolid fins store terminal vertices

For the disclosed SOLIDWORKS 2026 rectangular partitions, follow the fin's
forward link around each loop. Read the starting vertex from the mate and
the terminal vertex from the current fin.

The earlier decoder followed the backward link and used each fin's own
vertex as its start. This produced closed inward loops. The corners and
absolute volume still matched the source. Check signed volume when
verifying winding in the target schema.
[Measured native part and SDK comparison](../../../../../../../re/solidworks/records/SolidworksCurrentFinOrientation2026.md)
[Generated and native comparison](../../../../../../../re/solidworks/records/GeneratedRectanglePartition2026.md#standalone-archive-attachment)
