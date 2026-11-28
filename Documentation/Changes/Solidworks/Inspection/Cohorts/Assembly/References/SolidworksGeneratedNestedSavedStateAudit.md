# Audit persisted generated nested assembly state

The typed research auditor compares the first generated nested assembly's immutable files with all three actual native-saved derivatives. It checks linked configuration maps, selected target and stamp state, CMgrHdr2 summaries, each header copy and the persisted driving depth.

All 36 scoped stream round trips passed. The active depth persisted its `6.8 → 10.3 mm` edit, the two parents retained the saved child stamps, and their occurrence bounds matched the actual child-local boxes. Header count copies recorded distinct native save contexts. [Comparison and usage](../../../../../../../re/solidworks/records/GeneratedNestedAssemblySavedState2026.md) · [Header-count gotcha](../../../../../../Gotchas/Conversion/Solidworks/Archive/ExternalReferences/NestedSaveHeaderCountsUseDocumentContext.md)
