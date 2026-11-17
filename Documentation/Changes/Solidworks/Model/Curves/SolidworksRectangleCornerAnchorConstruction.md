# SOLIDWORKS rectangle corner anchor construction

The SOLIDWORKS 2026 research builder accepts a single origin-corner dimensioned Front Plane blind extrusion through `construct_part(..., rectangle_anchor="corner")`. The ordinary four-edge contour owns the body. A separate typed external sketch point and coincidence bind the first vertex to the part's actual Origin feature. The standard unanchored path stays byte-identical for the exercised request.

Two fresh guarded builds produced identical bytes with zero runtime input reads. Eight non-XML streams round-tripped with the real Config map, and centered or off-origin requests were rejected.

The disclosed native comparison verified independent width and height edits with a fully constrained sketch, the source's 25 feature rows and one matching solid. Both edited files saved and reopened successfully. All 165 numeric checks and both controls passed. The pre-writer held-outs and the public adapter's writer capability remain open. [Native receipt](../../../../../re/solidworks/measurements/2026/GeneratedRectangleAnchorNative01.json)

[Field and constructor evidence](../../../../../re/solidworks/records/RectangleCornerAnchorConstruction2026.md) · [Guarded discovery receipt](../../../../../re/solidworks/measurements/2026/GeneratedRectangleAnchorGuard01.json)
