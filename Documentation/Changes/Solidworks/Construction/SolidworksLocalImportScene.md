# Authored SOLIDWORKS local import scenes

The internal SOLIDWORKS 2026 SP05.2 local prism constructor can accept an
ordered scene with one authored ambient light and three directional lights.
`MakeBareImport(..., LightValues=scene)` uses their typed names, creation
times, colours, switches, coefficients and directions. The existing
single-ambient call remains available. Ambiguous input and unsupported
member lists are rejected before archive construction.

Three disclosed source projections retain their typed scene values, local
geometry and feature labels during guarded construction. A same-destination
contrast changes five graph and header streams and preserves the geometry
and rollback data. Native checks and the remaining source boundary are
tracked in the [measurement record](../../../../re/solidworks/records/ImportedLocalScene2026.md).
