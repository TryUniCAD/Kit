# Read a saved part's assigned physical material

For the qualified ordinary SOLIDWORKS 2026 part profile,
`open_document` returns a `MaterialRecord` with the verified name and
density in kg/m³. The selected design body's `material_id` links to
that record. Its `solidworks.assigned_part_material` attribute retains
the selected configuration, native catalog, material ID, body atom
and producing feature.

The reader requires agreement between the version-19000 part and
configuration owners, the active Parasolid solid, and the exact
`MATERIALTREE` material and configuration rows. Both strict read
modes check these owners. Design-only reads omit the returned B-rep.

The material color stays unset while appearance and complete catalog
properties remain unresolved. Contradictory assignments produce a
diagnostic. The public registry and native writers refuse incomplete
assignments before touching the destination.

Fourteen guarded reads across seven previously measured SOLIDWORKS 2026
SP05.2 saves preserve the linked assignment in both modes. The shared
queue case covers the independently authored assigned part, an
unassigned control, an invalid material claim and twelve write refusals.

[Adapter guide](../../../../Reference/Adapters/Solidworks.md) ·
[Archive ownership and proof](../../../../../re/solidworks/records/SdkAssignedPartRead2026.md)
