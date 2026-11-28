# Assembly occurrence bounds merge spheres

The embedded assembly bounding-box record stores an enclosing sphere and axis-aligned corners. The two use separate calculations. When SOLIDWORKS 2026 unions placed occurrences, it combines the corner extrema and merges the placed spheres. If the merged sphere is sufficiently larger than the distance to the farthest corner, it substitutes the sphere of the union's axis-aligned box. The A14 discovery assembly retains a shifted sphere center, which differs from its box midpoint.

Transform each child-local box into the parent frame before accumulating occurrences. Preserve the child radius through the rigid placement. Apply the sphere merge and its tightening condition at each union because later occurrences use the preceding sphere. [Native union formula and readback](../../../../../../re/solidworks/records/OrdinaryOccurrenceConstruction2026.md#generated-ordinary-occurrence-process)
