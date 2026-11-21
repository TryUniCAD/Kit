# Ordinary blind cuts use the instant extrusion class

SOLIDWORKS 2026 SP05.2 wrote `moICE_c` for the three disclosed ordinary blind
pockets authored through `FeatureCut4`. The class uses the same serializer
entry as `moExtrusion_c` and has its own constructor and cut state.

Identify the class through the pinned source archive and native dispatch. Keep
the cut's selected sketch, affected-body records and driving distance linked
to their actual owners. The known blind-boss builder lacks the measured body
selection graph. [Blind-cut archive evidence](../../../../../../re/solidworks/records/OrdinaryBlindCutConstruction2026.md)
