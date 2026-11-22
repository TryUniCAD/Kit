# Read a saved part's assigned physical material

For the qualified ordinary SOLIDWORKS 2026 part profile,
`open_document` reports the active material on
`DesignBody.attributes["solidworks.assigned_part_material"]`. The
record includes the selected configuration, native material catalog,
name and ID, density in kg/m³, native body atom and producing feature.

The reader requires agreement between the version-19000 part and
configuration owners, the active Parasolid solid, and the exact
`MATERIALTREE` material and configuration rows. Both strict read
modes check these owners. Design-only reads omit the returned B-rep.

The physical evidence and the neutral appearance are separate. The
reader reports unresolved appearance and catalog properties instead
of selecting a color. Contradictory or unsupported assignment
evidence produces an explicit diagnostic. Ordinary unassigned
parts keep their previous read behavior.

Fourteen guarded reads across seven previously measured SOLIDWORKS 2026
SP05.2 saves preserve the linked assignment in both modes. Two reads of
the unassigned control match the previous main. The shared queue
regression uses an independently supplied invalid material claim on a
tracked unassigned part. Named material writing remains pending.

[Adapter guide](../../../../Reference/Adapters/Solidworks.md) ·
[Archive ownership and proof](../../../../../re/solidworks/records/SdkAssignedPartRead2026.md)
