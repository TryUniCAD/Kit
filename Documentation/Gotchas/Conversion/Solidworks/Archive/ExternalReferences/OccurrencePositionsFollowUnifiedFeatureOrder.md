# Occurrence positions follow the unified feature order

The persistent feature identifier identifies an occurrence across native archives. Its placement in the feature tree uses a separate counter. SOLIDWORKS 2026 records the occurrence's zero-based position in the unified feature list before the save routine separates occurrences into Config-0 and leaves the standard assembly roots in ResolvedFeatures.

Build the occurrence ordinal from the actual feature sequence before splitting it. In the ordinary assembly witness, fifteen standard feature roots precede the occurrences and the mate group follows them. The first occurrence therefore uses position 15. The configuration's external-feature path uses its separately allocated persistent feature identifier.

On load, `moConcept_c::mergeFeatureList` uses the stored ordinal to find a position in the unified list and inserts the occurrence before that position. It appends the occurrence if the position is outside the list. The A14 native control has occurrence ids 24 and 25 and ordinals 15 and 16. [Native list separation and restoration evidence](../../../../../../re/solidworks/records/OrdinaryOccurrenceConstruction2026.md#archive-ownership)
