# SOLIDWORKS empty drawing appearance state

The ordinary version-19000 drawing Definition reader now accepts a present, genuinely empty appearance manager while preserving its exact unsigned64 allocation counter and original signed32 wire halves. The existing absent-manager branch remains supported. Populated rows, invalid words, invalid counts, mismatches, and other presence values remain unsupported.

Internal consumers can use `ReadAppearState(document, 19000)` to obtain `AppearanceState.ManagerOnWire` and `NextAppearanceId`. All original archive fields remain on the typed graph. Existing drawing constructors, footer/CLSID checks, linked-model guards, and public writer registration are unchanged.

Independent root verification passed the 43-worker prior cohort, a real generated-drawing component process with four counter-persistence cases and fifteen rejected invalid/populated cases, and source/input immutability. Both exact disclosed originals advance to the unchanged root-ownership/model-link rejection. They remain incomplete normal reads; this adds no original writer or native/held-out qualification.

The [field and native proof](../../../../../../re/solidworks/records/DrawingEmptyAppearanceAdmission2026.md), [revision-bound receipt](../../../../../../re/solidworks/measurements/2026/DrawingEmptyAppearanceReader01.json), and [presence gotcha](../../../../../Gotchas/Conversion/Solidworks/Archive/Drawings/Qualification/AppearancePresenceDoesNotMeanPopulatedData.md) record the exact boundary.
