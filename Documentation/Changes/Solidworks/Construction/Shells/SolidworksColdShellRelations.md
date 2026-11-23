# Preserve constrained rectangle stock in a cold shell

The internal SOLIDWORKS shell constructor now keeps four actual horizontal or vertical line relations and four shared corner coincidences. It checks each original endpoint role before deriving the canonical native contour. The strict shell reader resolves those same axis owners and corners, and preserves both independent live drivers and the selected upper cap.

Three [guarded model comparisons](../../../../../re/solidworks/records/SdkColdShellRelations2026.md) preserve the two disclosed source profiles and an independent translated rectangle. Twelve private recompilations reproduce the three candidates from strict reads and inspection JSON. Altered relations, direct and registry writes and full saved-source compilation refuse at their existing boundaries. Native and held-out qualification for these candidates remain pending.
