# Read saved equal-distance and two-distance edge chamfers

The strict SOLIDWORKS 2026 part reader restores the chamfer's selected stock
edge and incident face, shared D1 setback or independent D1 and D3 setbacks,
and the editable Front-plane rectangular stock that created the body.
The stock preserves its selected-empty first-creator scope when the chamfer
is the sole direct terminal modifier.

Use `open_document` for an ordinary saved part with the active `Default`
configuration. The reader checks the active partition and rollback against
the actual archive owners, and retains the native B-rep. Pass
`include_brep=False` for the same history and drivers without geometry.
The verified input profile has one forward blind stock and one ordinary
chamfer on a straight convex edge. Native write qualification remains
a separate requirement.

[Exact saved-source proof](../../../../../re/solidworks/records/ChamferDistancePairSavedRead2026.md)
