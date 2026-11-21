# A resolved mate group can have empty wire children

The resolved `moMateGroup_c` may have an empty `f60` child list while the native FeatureManager shows a concentric mate inside it. SOLIDWORKS 2026 stores the actual mate list separately in `Contents/Config-0-MatesList` and appends it to the real group on load.

Resolve the actual top-level group through the linked archive and bind the admitted member through the complete separate list. Refuse an ambiguous group, active group-specific state or unqualified contents. [Native save and load](../../../../../../re/solidworks/records/AssemblyMatesList2026.md) · [Disclosed group verification](../../../../../../re/solidworks/records/ConcentricMateGroupRead2026.md)
