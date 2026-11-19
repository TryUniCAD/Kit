# Concentric snapshot IDs need their actual owners

A concentric mate has separate active face references and faceted support snapshots. Similar small integers in those objects do not share an identity domain.

The pinned native getters name `moFacetedData.f40` as the kernel face node ID, `f50` as the body atom ID and `f54` as the feature ID. The active surface representation's `moFR` selects the extrusion feature and that feature's creation-log epoch. Its `f38` belongs to the generating sketch arc's permanent marker `f08`; the arc's creation ID `f0c` is separate even when both are one in an ordinary circle.

Resolve the real extrusion → profile → sketch arc and extrusion → body atom paths. Compute the single-surface snapshot text from those actual owners and the documented native text format. Do not substitute an archive map index, neutral face-array index, sketch feature ID or repeated observed number. Snapshot omission and `-1` recovery require their own native proof; the default constructor alone does not establish them.

[Exact native bindings and source audit](../../../../../../re/solidworks/records/ConcentricFaceIdentity2026.md) · [Process evidence](../../../../../../re/solidworks/measurements/2026/ConcentricFaceIdentity01.json)
