# Inactive Pad length survives source read

A one-direction FreeCAD Pad can retain a second length. The three disclosed files have an inactive 10 mm `Length2` alongside the live 20 mm length. Equal current geometry does not establish that the second editable value can be replaced.

The ordinary SOLIDWORKS one-direction graph has two distinct dimension owners. Its default constructor fills the dormant D2 with the primary depth. A native-saved example preserves dormant D2 across an independent active D1 edit. Keep the second source value separate from the direction mode and require a qualified native owner for it before allowing whole-source conversion.

[FreeCAD graph comparison](../../../../../re/solidworks/records/FcstdCornerPlan2026.md) · [Internal constructor proof](../../../../../re/solidworks/records/SdkBlindDormantDepth2026.md) · [Native saved-state comparison](../../../../../re/solidworks/records/GeneratedNestedAssemblySavedState2026.md)
