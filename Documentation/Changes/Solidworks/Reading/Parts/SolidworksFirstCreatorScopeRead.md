# Preserve selected-empty scope on a cache-free rectangular boss

The strict SOLIDWORKS part reader exposes the first rectangular boss as a
`create` extrusion with `ScopedExtrusionFeature.ScopeMode == "first_creator"`
when the native feature selects existing bodies and there are zero prior
bodies to select. The selected and affected lists are empty. The mode requires
an active root solid, its actual profile plane and live positive blind depth.
The strict reader checks the linked feature flags and absence of native body
wrappers before reconstructing the body.

Both disclosed selected-empty inputs and their matched all-scope controls
retain the same solid geometry and three live drivers. Their neutral JSON
round trips preserve the mode and design-body ownership. The four edited
SOLIDWORKS derivatives retain their measured geometry through the native
cache decoder. Their stored scope is verified in a separate typed audit.
The scoped feature projection is qualified for cache-free readback.

[Process evidence and reproduction](../../../../../re/solidworks/records/FirstCreatorScopeRead2026.md)
